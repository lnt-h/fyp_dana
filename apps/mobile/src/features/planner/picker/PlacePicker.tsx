/**
 * SCR-028 Place picker (full screen): published places of the trip's city only (API-010), for Add a stop, Replace a
 * stop or must-see selection. Places already in the trip are listed with a badge and cannot be chosen again.
 * No distance hint is shown (OQ-110).
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { FlatList, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { Chip, CircleButton, Icon, Photo, Skeleton, categoryIcon } from '../../../components/ui';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import { currentLocale } from '../../../i18n';
import { listCategories } from '../../../lib/api/source';
import { searchCityPlaces } from '../../../lib/api/sourcePlanning';
import type { Category, Place, Uuid } from '../../../lib/api/types';
import { categoryColor, colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { InlineBanner, PillButton, editTokens } from '../edit/EditUI';
import { editErrorCopy } from '../edit/errorCopy';
import type { PendingEdit } from '../edit/draftStore';
import type { EditOutcome } from '../edit/usePreviewEditor';

export const MUST_SEE_LIMIT = 10;
const THUMB = 64;

export type PickedPlace = Pick<Place, 'id' | 'name'>;

export type PickerMode =
  | { kind: 'add'; dayIndex: number }
  | { kind: 'replace'; stopId: Uuid; number: number; name: string; /** Null when replacing a WEB_UNVERIFIED stop. */ placeId: Uuid | null }
  | { kind: 'mustSee'; selected: PickedPlace[]; onChange: (next: PickedPlace[]) => void };

type Props = {
  mode: PickerMode | null;
  cityId: Uuid | null;
  cityName: string;
  /** `place_id` → day index for every stop already in the trip (shown with a badge, not choosable). */
  planned?: Record<Uuid, number>;
  offline?: boolean;
  /** Add/replace: applies the edit; the picker closes on success and shows the error otherwise. */
  onChoose?: (place: Place) => Promise<EditOutcome | null>;
  onClose: () => void;
  /** Add mode: the day already has the maximum number of stops. */
  dayFull?: boolean;
  /**
   * Unresolved proposal edit (ADR-009): while it exists no new edit can be sent, so rows are disabled and the picker
   * itself offers Retry / Discard (Discard only when the server refused it for good).
   */
  pending?: PendingEdit;
  onRetryPending?: () => void;
  onDiscardPending?: () => void;
};

export function PlacePicker({ mode, cityId, cityName, planned = {}, offline = false, onChoose, onClose, dayFull = false, pending, onRetryPending, onDiscardPending }: Props) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const reducedMotion = useReducedMotion();
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<string | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [results, setResults] = useState<Place[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [busyId, setBusyId] = useState<Uuid | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const requestId = useRef(0);
  const visible = !!mode;

  useEffect(() => {
    if (!visible) { setQuery(''); setCategory(null); setResults(null); setError(null); setBusyId(null); return; }
    listCategories().then(setCategories).catch(() => setCategories([]));
  }, [visible]);

  useEffect(() => {
    if (!visible || !cityId) return;
    const id = ++requestId.current;
    setFailed(false);
    setResults(null);
    const timer = setTimeout(() => {
      searchCityPlaces(cityId, query.trim() || undefined, category)
        .then(items => { if (id === requestId.current) setResults(items.slice(0, 20)); })
        .catch(() => { if (id === requestId.current) { setResults([]); setFailed(true); } });
    }, query ? 250 : 0);
    return () => clearTimeout(timer);
  }, [attempt, category, cityId, query, visible]);

  const choose = useCallback(async (place: Place) => {
    if (!mode) return;
    if (mode.kind === 'mustSee') {
      const chosen = mode.selected.some(item => item.id === place.id);
      if (chosen) mode.onChange(mode.selected.filter(item => item.id !== place.id));
      else if (mode.selected.length < MUST_SEE_LIMIT) mode.onChange([...mode.selected, { id: place.id, name: place.name }]);
      return;
    }
    if (!onChoose) return;
    setBusyId(place.id);
    setError(null);
    const outcome = await onChoose(place);
    setBusyId(null);
    if (!outcome) return;
    if (outcome.ok) { onClose(); return; }
    setError(outcome.status === 'conflict' ? t('proposal.edit.conflictTitle') : editErrorCopy(t, outcome.code));
  }, [mode, onChoose, onClose, t]);

  if (!mode) return null;

  const title = mode.kind === 'add'
    ? t('proposal.picker.titleAdd', { day: mode.dayIndex })
    : mode.kind === 'replace' ? t('proposal.picker.titleReplace', { number: mode.number }) : t('proposal.picker.titleMustSee');
  const mustSee = mode.kind === 'mustSee';
  // An edit still applying (e.g. this picker's own choice) counts as busy; a failed one blocks choosing until resolved.
  const blockedByPending = !mustSee && !!pending;
  const busy = busyId !== null || (!mustSee && pending?.status === 'applying');
  const full = mustSee && mode.selected.length >= MUST_SEE_LIMIT;
  const currentDay = mode.kind === 'add' ? mode.dayIndex : null;
  const vi = currentLocale() === 'vi';

  function badgeFor(place: Place): string | null {
    if (mustSee) return null;
    if (mode?.kind === 'replace' && place.id === mode.placeId) return t('proposal.picker.current');
    const day = planned[place.id];
    if (day == null) return null;
    return day === currentDay ? t('proposal.picker.inThisDay') : t('proposal.picker.inDay', { day });
  }

  return <Modal animationType={reducedMotion ? 'none' : 'slide'} onRequestClose={() => { if (busyId === null) onClose(); }} presentationStyle="fullScreen" visible={visible}>
    <StatusBar style="dark" />
    <View accessibilityViewIsModal style={[k.screen, { paddingTop: insets.top }]}>
      <View style={k.header}>
        <CircleButton accessibilityLabel={t('proposal.picker.close')} disabled={busyId !== null} icon="back" onPress={onClose} size={44} tone="tint" />
        <View style={k.headerCopy}>
          <Text accessibilityRole="header" numberOfLines={2} style={k.title}>{title}</Text>
          {mode.kind === 'replace' ? <Text numberOfLines={1} style={k.subtitle}>{t('proposal.picker.replacing', { name: mode.name })}</Text> : null}
          {mustSee ? <Text accessibilityLiveRegion="polite" style={k.subtitle}>{full ? t('proposal.picker.max') : t('proposal.picker.count', { count: mode.selected.length })}</Text> : null}
        </View>
        {mustSee ? <PillButton label={t('proposal.picker.done')} onPress={onClose} tone="primary" /> : null}
      </View>

      <View style={k.pad}>
        <View style={[k.search, offline && k.searchDisabled]}>
          <Icon color={colors.textMuted} name="search" size={20} />
          <TextInput
            accessibilityLabel={t('proposal.picker.search', { city: cityName })}
            autoCorrect={false}
            editable={!offline}
            maxLength={120}
            onChangeText={setQuery}
            placeholder={t('proposal.picker.search', { city: cityName })}
            placeholderTextColor={colors.textMuted}
            returnKeyType="search"
            style={k.input}
            value={query}
          />
          {query ? <Pressable accessibilityLabel={t('proposal.picker.clear')} accessibilityRole="button" onPress={() => setQuery('')} style={k.clear}>
            <Text style={k.clearGlyph}>×</Text>
          </Pressable> : null}
        </View>
        <Text style={k.scope}>{t('proposal.picker.scope', { city: cityName })}</Text>
      </View>

      {categories.length ? <ScrollView accessibilityLabel={t('proposal.picker.categories')} contentContainerStyle={k.chips} horizontal showsHorizontalScrollIndicator={false} style={k.chipScroll}>
        <Chip label={t('proposal.picker.all')} onPress={() => setCategory(null)} selected={category === null} />
        {[...categories].sort((a, b) => a.sort_order - b.sort_order).map(item => <Chip
          key={item.code}
          icon={categoryIcon(item.code)}
          tone={categoryColor(item.code)}
          label={vi ? item.name_vi : item.name_en}
          onPress={() => setCategory(current => current === item.code ? null : item.code)}
          selected={category === item.code}
        />)}
      </ScrollView> : null}

      {offline ? <InlineBanner style={k.banner} title={t('proposal.picker.offline')} tone="warning" /> : null}
      {dayFull && currentDay ? <InlineBanner style={k.banner} title={t('proposal.picker.dayFull', { day: currentDay })} tone="warning" /> : null}
      {blockedByPending && pending && pending.status !== 'applying' ? <InlineBanner
        actions={pending.status === 'rejected'
          ? <PillButton label={t('proposal.edit.discard')} onPress={() => onDiscardPending?.()} tone="primary" />
          : <>
            <PillButton icon="refresh" label={pending.status === 'conflict' ? t('proposal.edit.reloadReapply') : t('proposal.edit.retry')} onPress={() => onRetryPending?.()} tone="primary" />
            <PillButton label={t('proposal.edit.discard')} onPress={() => onDiscardPending?.()} />
          </>}
        body={pending.status === 'rejected' ? t('proposal.edit.rejectedBody') : t('proposal.picker.pendingBody')}
        style={k.banner}
        title={pending.status === 'conflict' ? t('proposal.edit.conflictTitle') : pending.status === 'expired' ? t('proposal.edit.expiredTitle') : editErrorCopy(t, pending.errorCode)}
        tone="error"
      /> : error ? <InlineBanner body={t('proposal.edit.kept')} style={k.banner} title={error} tone="error" /> : null}

      {results === null
        ? <View accessibilityLabel={t('proposal.picker.loading')} accessibilityLiveRegion="polite" style={k.list}>
          {[0, 1, 2].map(index => <View key={index} style={k.row}>
            <Skeleton height={THUMB} radius={radii.iconTile} width={THUMB} />
            <View style={k.rowCopy}><Skeleton height={18} width="70%" /><Skeleton height={14} width="45%" /></View>
          </View>)}
        </View>
        : <FlatList
          ListEmptyComponent={failed
            ? <InlineBanner actions={<PillButton icon="refresh" label={t('proposal.picker.retry')} onPress={() => setAttempt(value => value + 1)} />} style={k.banner} title={t('proposal.picker.error')} tone="error" />
            : <View accessibilityLiveRegion="polite" style={k.empty}>
              <View style={k.emptyIcon}><Icon color={colors.tealText} name="search" size={26} /></View>
              <Text style={k.emptyTitle}>{t('proposal.picker.empty', { city: cityName })}</Text>
              <Text style={k.emptyBody}>{t('proposal.picker.emptyBody')}</Text>
            </View>}
          contentContainerStyle={[k.list, { paddingBottom: insets.bottom + spacing.xl }]}
          data={results}
          keyExtractor={item => item.id}
          keyboardDismissMode="on-drag"
          keyboardShouldPersistTaps="handled"
          renderItem={({ item }) => {
            const badge = badgeFor(item);
            const chosen = mustSee && mode.selected.some(selected => selected.id === item.id);
            const disabled = offline || busy || blockedByPending || !!badge || (mode.kind === 'add' && dayFull) || (mustSee && full && !chosen);
            return <PlaceRow
              badge={badge}
              busy={busyId === item.id}
              chosen={chosen}
              disabled={disabled}
              mustSee={mustSee}
              onChoose={() => choose(item)}
              place={item}
            />;
          }}
        />}
    </View>
  </Modal>;
}

function PlaceRow({ place, badge, chosen, busy, disabled, mustSee, onChoose }: {
  place: Place; badge: string | null; chosen: boolean; busy: boolean; disabled: boolean; mustSee: boolean; onChoose: () => void;
}) {
  const { t } = useTranslation();
  const other = place.name !== place.name_vi ? place.name_vi : null;
  const duration = place.visit_minutes_suggested ? t('proposal.picker.minutes', { count: place.visit_minutes_suggested }) : null;
  const secondary = [other, duration].filter(Boolean).join(' · ');
  return <View accessibilityLabel={[place.name, other, duration, badge].filter(Boolean).join(', ')} style={[k.row, !!badge && k.rowMuted]}>
    <View style={k.thumb}>
      <Photo categoryCode={place.category_code} height={THUMB} iconSize={26} image={place.thumbnail} name={place.name} transition={150} variant="thumb" width={THUMB} />
    </View>
    <View style={k.rowCopy}>
      <Text numberOfLines={2} style={k.name}>{place.name}</Text>
      {secondary ? <Text numberOfLines={1} style={k.secondary}>{secondary}</Text> : null}
      {badge ? <View style={k.badge}><Text style={k.badgeText}>{badge}</Text></View>
        : place.short_description ? <Text numberOfLines={1} style={k.description}>{place.short_description}</Text> : null}
    </View>
    {badge ? null : <PillButton
      accessibilityLabel={t('proposal.picker.chooseA11y', { name: place.name })}
      disabled={disabled && !chosen}
      icon={chosen ? 'check' : busy ? undefined : 'plus'}
      label={busy ? t('proposal.sheet.applying') : chosen ? t('proposal.picker.chosen') : t('proposal.picker.choose')}
      onPress={onChoose}
      selected={mustSee ? chosen : undefined}
      tone={mustSee ? 'default' : 'primary'}
    />}
  </View>;
}

const k = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.canvas },
  header: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.xs },
  headerCopy: { flex: 1, minWidth: 0 },
  title: { ...typography.headline },
  subtitle: { fontFamily: fonts.medium, fontSize: 14, color: colors.textMuted, marginTop: 1 },
  pad: { paddingHorizontal: spacing.lg, paddingTop: spacing.xs },
  search: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 54, borderRadius: radii.field, borderWidth: 1.5, borderColor: editTokens.border, paddingLeft: spacing.md, backgroundColor: colors.white },
  searchDisabled: { backgroundColor: editTokens.canvas },
  input: { flex: 1, fontFamily: fonts.medium, fontSize: 16, color: colors.deepOcean, paddingVertical: 12 },
  clear: { width: MIN_TOUCH, height: MIN_TOUCH, alignItems: 'center', justifyContent: 'center' },
  clearGlyph: { fontSize: 24, lineHeight: 26, color: colors.textMuted },
  scope: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.textMuted, marginTop: spacing.xs },
  chipScroll: { flexGrow: 0, marginTop: spacing.sm },
  chips: { gap: spacing.xs, paddingHorizontal: spacing.lg, paddingVertical: 4 },
  banner: { marginHorizontal: spacing.lg, marginTop: spacing.sm },
  list: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm, gap: 2 },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.sm, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: editTokens.border },
  rowMuted: { opacity: 0.85 },
  thumb: { width: THUMB, height: THUMB, borderRadius: radii.iconTile, overflow: 'hidden', backgroundColor: colors.surfaceTint },
  rowCopy: { flex: 1, minWidth: 0, gap: 3 },
  name: { fontFamily: fonts.bold, fontSize: 16, lineHeight: 21, color: colors.ink },
  secondary: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.textMuted },
  description: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.textMuted },
  badge: { alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 3, borderRadius: radii.chip, backgroundColor: colors.surfaceTint },
  badgeText: { fontFamily: fonts.bold, fontSize: 12, color: colors.accentText },
  empty: { alignItems: 'center', paddingVertical: spacing.xxl, paddingHorizontal: spacing.lg },
  emptyIcon: { width: 60, height: 60, borderRadius: 30, backgroundColor: colors.surfaceTint, alignItems: 'center', justifyContent: 'center' },
  emptyTitle: { ...typography.bodyStrong, textAlign: 'center', marginTop: spacing.sm },
  emptyBody: { ...typography.caption, fontSize: 14, textAlign: 'center', marginTop: 2 },
});
