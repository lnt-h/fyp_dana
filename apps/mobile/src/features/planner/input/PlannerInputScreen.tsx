import { useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { useAccount, type Interest } from '../../account/AccountContext';
import { currentLocale } from '../../../i18n';
import { ApiError, createTrip, getPreferences, listCategories, listCities } from '../../../lib/api/source';
import type { Category, City, ClarificationRequired, Pace, PlanPreviewCreate, TravelMode, Uuid } from '../../../lib/api/types';
import { DEFAULT_CITY_CODE } from '../../../lib/api/types';
import { Icon, PrimaryButton, SecondaryButton, Skeleton, categoryIcon, travelModeIcon } from '../../../components/ui';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { errorCopy, toErrorDetail } from '../progress/errorCopy';
import { setPlanRequest } from '../progress/planRequestStore';
import {
  acknowledgeAiNotice, isAiNoticeAcknowledged, readDraft, takePendingView, writeDraft, type InputMode, type PlannerDraft, type PlannerView,
} from './draftStore';
import { MUST_SEE_MAX, MustSeePicker } from './MustSeePicker';
import {
  Banner, Chip, ChipRow, CityTiles, FieldError, IntroCard, PickerField, PlannerShell, Segmented, SectionLabel, UserBubble, p, tone,
} from './PlannerUI';
import { dateFromIso, dateFromLocalTime, dayMonthYear, minutesOf, todayVn, vnIsoDate, vnLocalTime, weekdayOf } from './vnTime';

const TEXT_MAX = 500;
const COUNTER_FROM = 400;
const paces: Pace[] = ['RELAXED', 'BALANCED', 'PACKED'];
const travelModes: TravelMode[] = ['WALK', 'DRIVE'];
const dayCounts = [1, 2, 3] as const;
/** Saved profile interests (onboarding) → catalog category codes, used only when API-004 has none. */
const profileInterestCodes: Record<Interest, string> = { Beach: 'beach', Culture: 'heritage', Food: 'market', Nature: 'nature' };

const emptyDraft = (): PlannerDraft => ({
  cityId: null, dayCount: null, dayEnd: '18:00', dayStart: '08:30', interests: [], mode: 'form', modes: ['WALK'], mustSee: [],
  pace: 'BALANCED', prefilled: false, requestText: '', startDate: null,
});

type FieldErrors = Partial<Record<'startDate' | 'dayCount' | 'hours' | 'modes' | 'text', string>>;

export function PlannerInputScreen() {
  const { t, i18n } = useTranslation();
  const vi = i18n.resolvedLanguage === 'vi';
  const { profile } = useAccount();
  const [draft, setDraftState] = useState<PlannerDraft>(() => readDraft() ?? emptyDraft());
  const [view, setView] = useState<PlannerView>(() => takePendingView() ?? { kind: 'input' });
  const [cities, setCities] = useState<City[] | null>(null);
  const [categories, setCategories] = useState<Category[] | null>(null);
  const [prefillShown, setPrefillShown] = useState(draft.prefilled);
  const [noticeAcked, setNoticeAcked] = useState(isAiNoticeAcknowledged);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const update = (changes: Partial<PlannerDraft>) => setDraftState(previous => {
    const next = { ...previous, ...changes };
    writeDraft(next);
    return next;
  });

  useEffect(() => {
    let alive = true;
    listCities().then(items => {
      if (!alive) return;
      setCities(items);
      setDraftState(previous => {
        if (previous.cityId) return previous;
        const next = { ...previous, cityId: (items.find(city => city.code === DEFAULT_CITY_CODE) ?? items[0])?.id ?? null };
        writeDraft(next);
        return next;
      });
    }).catch(() => alive && setSubmitError(errorCopy(t, 'network')));
    listCategories().then(items => alive && setCategories([...items].sort((x, y) => x.sort_order - y.sort_order))).catch(() => alive && setCategories([]));
    if (!draft.prefilled) {
      getPreferences().then(prefs => {
        if (!alive) return;
        const fromProfile = profile.interests.map(interest => profileInterestCodes[interest]);
        const interests = prefs.interest_category_codes.length ? prefs.interest_category_codes : fromProfile;
        const hadValues = Boolean(prefs.pace || interests.length || prefs.allowed_modes.length || prefs.day_start_time);
        setDraftState(previous => {
          const next: PlannerDraft = {
            ...previous,
            dayEnd: prefs.day_end_time ?? previous.dayEnd,
            dayStart: prefs.day_start_time ?? previous.dayStart,
            interests: interests.length ? interests : previous.interests,
            modes: prefs.allowed_modes.length ? prefs.allowed_modes : previous.modes,
            pace: prefs.pace ?? previous.pace,
            prefilled: true,
          };
          writeDraft(next);
          return next;
        });
        if (prefs.ai_notice_acknowledged_at) { acknowledgeAiNotice(); setNoticeAcked(true); }
        setPrefillShown(hadValues);
      }).catch(() => undefined);
    }
    return () => { alive = false; };
    // Load once on mount; the draft and profile are read at that moment only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const city = cities?.find(item => item.id === draft.cityId) ?? null;
  const cityName = (item: City | null) => (item ? (vi ? item.name_vi : item.name_en) : '');
  const dateLocale = vi ? 'vi-VN' : 'en-GB';
  const formatDate = (date: string) => `${t(`planner.weekday.${weekdayOf(date) as 0 | 1 | 2 | 3 | 4 | 5 | 6}`)}, ${dayMonthYear(date)}`;
  const today = todayVn();
  const textLength = draft.requestText.length;

  const interestNames = useMemo(() => (categories ?? []).filter(category => draft.interests.includes(category.code))
    .map(category => (vi ? category.name_vi : category.name_en)), [categories, draft.interests, vi]);

  function validateForm(): FieldErrors {
    const next: FieldErrors = {};
    if (!draft.startDate) next.startDate = t('planner.validation.startDate');
    else if (draft.startDate < today) next.startDate = t('planner.validation.startPast');
    if (!draft.dayCount) next.dayCount = t('planner.validation.days');
    if (minutesOf(draft.dayEnd) <= minutesOf(draft.dayStart)) next.hours = t('planner.validation.hours');
    if (draft.modes.length === 0) next.modes = t('planner.validation.modes');
    return next;
  }

  async function submit() {
    if (busy || !city) return;
    setSubmitError(null);
    const describing = draft.mode === 'describe' && view.kind === 'input';
    if (describing) {
      if (!draft.requestText.trim()) { setErrors({ text: t('planner.validation.text') }); return; }
      if (!noticeAcked) { acknowledgeAiNotice(); setNoticeAcked(true); }
      // Never guess the date or length from free text: ask for what is missing (FR-022).
      const missing: ClarificationRequired['missing_fields'] = [];
      if (!draft.startDate) missing.push('start_date');
      if (!draft.dayCount) missing.push('day_count');
      if (missing.length) { setErrors({}); setView({ clarification: { message: '', missing_fields: missing, outcome: 'CLARIFICATION_REQUIRED' }, kind: 'clarify' }); return; }
    }
    const fieldErrors = validateForm();
    setErrors(fieldErrors);
    if (Object.keys(fieldErrors).length > 0 || !draft.startDate || !draft.dayCount) {
      if (describing || view.kind !== 'input') setSubmitError(Object.values(fieldErrors)[0] ?? null);
      return;
    }
    setBusy(true);
    try {
      const trip = await createTrip({ city_id: city.id, day_count: draft.dayCount, start_date: draft.startDate });
      const body: PlanPreviewCreate = {
        expected_trip_revision: trip.revision,
        locale: currentLocale(),
        preferences: {
          allowed_modes: draft.modes,
          day_end_time: draft.dayEnd,
          day_start_time: draft.dayStart,
          interest_category_codes: draft.interests,
          must_see_place_ids: draft.mustSee.map(place => place.id),
          pace: draft.pace,
        },
        request_text: draft.requestText.trim() ? draft.requestText.trim().slice(0, TEXT_MAX) : null,
        source: 'GENERATE',
      };
      setPlanRequest({ body, city, trip });
      // The preview id is only known once the stream reports preview_ready; the progress route ignores this segment.
      router.replace({ params: { previewId: 'pending' }, pathname: '/plan/[previewId]' });
    } catch (error) {
      const detail = toErrorDetail(error);
      if (detail.code === 'unsupported_request') { setView({ kind: 'unsupported' }); return; }
      if (detail.code === 'validation_failed' && error instanceof ApiError) {
        const fields = (detail.context?.fields ?? {}) as Record<string, unknown>;
        setErrors({
          ...(fields.start_date ? { startDate: t('planner.validation.startDate') } : {}),
          ...(fields.day_count ? { dayCount: t('planner.validation.days') } : {}),
        });
      }
      setSubmitError(errorCopy(t, detail.code));
    } finally {
      setBusy(false);
    }
  }

  const setCity = (cityId: Uuid) => update({ cityId, mustSee: cityId === draft.cityId ? draft.mustSee : [] });

  const credit = city ? CITY_IMAGES[city.code]?.attribution_text : null;
  const cityPicker = (onPick: (item: City) => void, selectedId: string | null) => cities
    ? <>
      <CityTiles cities={cities} selectedId={selectedId} label={t('planner.city.label')} nameOf={cityName} onSelect={onPick} />
      {selectedId && credit ? <Text numberOfLines={1} style={styles.credit}>{t('planner.city.photoCredit', { credit })}</Text> : null}
    </>
    : <View style={styles.tileSkeletons}>{[0, 1, 2].map(key => <Skeleton key={key} width={128} height={164} radius={22} />)}</View>;

  const dateField = <PickerField hideLabel label={t('planner.date.label')} pickerTitle={t('planner.date.pickerTitle')} mode="date" locale={dateLocale}
    text={draft.startDate ? formatDate(draft.startDate) : null} placeholder={t('planner.date.placeholder')} error={errors.startDate}
    value={dateFromIso(draft.startDate ?? today)} minimumDate={dateFromIso(today)}
    onChange={date => { update({ startDate: vnIsoDate(date) }); setErrors(previous => ({ ...previous, startDate: undefined })); }} />;

  const dayPicker = <>
    <Segmented<number> role="radio" label={t('planner.days.label')} value={draft.dayCount} invalid={!!errors.dayCount}
      options={dayCounts.map(count => ({ label: t('planner.days.option', { count }), value: count }))}
      onChange={count => { update({ dayCount: count as 1 | 2 | 3 }); setErrors(previous => ({ ...previous, dayCount: undefined })); }} />
    <FieldError>{errors.dayCount}</FieldError>
  </>;

  /* ------------------------------------------------------------------ Clarification view */
  if (view.kind === 'clarify') {
    const missing = view.clarification.missing_fields;
    const answered = missing.every(field => (field === 'city' ? !!draft.cityId : field === 'start_date' ? !!draft.startDate : !!draft.dayCount));
    const summary = [
      !missing.includes('city') && cityName(city),
      !missing.includes('day_count') && draft.dayCount && t('planner.days.option', { count: draft.dayCount }),
      ...interestNames,
    ].filter(Boolean).join(' · ');
    return <PlannerShell title={t('planner.title')} onBack={() => setView({ kind: 'input' })}
      footer={<>
        {!answered && <Text style={styles.reason}>{t('planner.clarify.disabledReason')}</Text>}
        {!!submitError && <Text accessibilityRole="alert" style={[styles.reason, { color: tone.error }]}>{submitError}</Text>}
        <PrimaryButton label={busy ? t('planner.submit.creating') : t('planner.submit.create')} icon="sparkle" iconSize={16} loading={busy} disabled={!answered}
          accessibilityHint={answered ? undefined : t('planner.clarify.disabledReason')} onPress={() => void submit()} />
      </>}>
      {!!draft.requestText.trim() && <UserBubble text={draft.requestText.trim()} />}
      <IntroCard label={t('planner.intro.label')} body={missing.map(field => t(`planner.clarify.question.${field}`)).join(' ')} />
      {view.clarification.message ? <Text style={[p.hint, { marginBottom: spacing.xs }]}>{view.clarification.message}</Text> : null}
      {missing.includes('city') && <><SectionLabel>{t('planner.city.label')}</SectionLabel>{cityPicker(item => setCity(item.id), draft.cityId)}</>}
      {missing.includes('start_date') && <><SectionLabel>{t('planner.date.label')}</SectionLabel>{dateField}</>}
      {missing.includes('day_count') && <><SectionLabel>{t('planner.days.label')}</SectionLabel>{dayPicker}</>}
      {!!summary && <View style={styles.understood}>
        <Icon name="check" size={18} color={colors.tealText} strokeWidth={2.2} />
        <Text style={styles.understoodText}>{t('planner.clarify.understood', { summary })}</Text>
      </View>}
      <SecondaryButton label={t('planner.clarify.edit')} onPress={() => setView({ kind: 'input' })} style={styles.secondary} />
    </PlannerShell>;
  }

  /* ------------------------------------------------------------------ Unsupported view */
  if (view.kind === 'unsupported') {
    return <PlannerShell title={t('planner.title')} onBack={() => setView({ kind: 'input' })}>
      <Banner tone="warning">{t('planner.unsupported.body')}</Banner>
      <SectionLabel>{t('planner.unsupported.pickCity')}</SectionLabel>
      {cityPicker(item => { setCity(item.id); update({ mode: 'form' }); setView({ kind: 'input' }); }, null)}
      <SecondaryButton label={t('planner.unsupported.edit')} onPress={() => { update({ mode: 'describe' }); setView({ kind: 'input' }); }} style={styles.secondary} />
    </PlannerShell>;
  }

  /* ------------------------------------------------------------------ Input view (form / describe) */
  const describing = draft.mode === 'describe';
  const emptyText = describing && !draft.requestText.trim();
  const ctaLabel = busy ? t('planner.submit.creating') : describing ? t('planner.submit.continue') : t('planner.submit.create');
  const mustSeeFull = draft.mustSee.length >= MUST_SEE_MAX;

  return <PlannerShell title={t('planner.title')}
    footer={<>
      {emptyText && <Text style={styles.reason}>{t('planner.validation.text')}</Text>}
      {!!submitError && <Text accessibilityRole="alert" style={[styles.reason, { color: tone.error }]}>{submitError}</Text>}
      {/* The one sparkle left in the app: the "Tạo đề xuất" CTA (thin, 16 dp). */}
      <PrimaryButton label={ctaLabel} icon={describing ? undefined : 'sparkle'} iconSize={16} loading={busy} disabled={!city || emptyText}
        accessibilityHint={emptyText ? t('planner.validation.text') : undefined} onPress={() => void submit()} />
    </>}>
    <IntroCard label={t('planner.intro.label')} body={t('planner.intro.body')} />
    <Segmented<InputMode> label={t('planner.mode.label')} value={draft.mode} onChange={mode => { update({ mode }); setErrors({}); setSubmitError(null); }}
      options={[{ label: t('planner.mode.form'), value: 'form' }, { label: t('planner.mode.describe'), value: 'describe' }]} />
    {prefillShown && <View style={styles.prefill}>
      <Icon name="check" size={16} color={colors.tealText} strokeWidth={2.4} />
      <Text style={styles.prefillText}>{t('planner.prefilled')}</Text>
    </View>}

    {describing ? <>
      <SectionLabel>{t('planner.describe.prompt')}</SectionLabel>
      <View style={[styles.textArea, !!errors.text && p.invalid]}>
        <TextInput multiline value={draft.requestText} maxLength={TEXT_MAX} accessibilityLabel={t('planner.describe.label')} accessibilityHint={t('planner.describe.hint')}
          placeholder={t('planner.describe.placeholder')} placeholderTextColor={colors.textMuted} textAlignVertical="top" style={styles.textInput}
          onChangeText={requestText => { update({ requestText }); if (errors.text) setErrors({}); }} />
        {textLength >= COUNTER_FROM && <Text accessibilityLiveRegion="polite" style={[styles.counter, textLength >= TEXT_MAX && { color: tone.error }]}>{t('planner.describe.counter', { count: textLength })}</Text>}
      </View>
      <Text style={p.hint}>{t('planner.describe.hint')}</Text>
      <FieldError>{errors.text}</FieldError>
      {!noticeAcked && <View style={{ marginTop: spacing.lg }}>
        <Banner tone="info" title={t('planner.notice.title')}
          action={<Pressable accessibilityRole="link" accessibilityLabel={t('planner.notice.learnMore')} onPress={() => router.push('/settings')} style={styles.learnMore}>
            <Text style={p.link}>{t('planner.notice.learnMore')}</Text>
            <Icon name="chevron-right" size={16} color={colors.tealText} />
          </Pressable>}>
          {t('planner.notice.body')}
        </Banner>
      </View>}
    </> : <>
      <SectionLabel>{t('planner.city.label')}</SectionLabel>
      {cityPicker(item => setCity(item.id), draft.cityId)}

      <SectionLabel>{t('planner.date.label')}</SectionLabel>
      {dateField}

      <SectionLabel>{t('planner.days.label')}</SectionLabel>
      {dayPicker}

      <SectionLabel>{t('planner.hours.label')}</SectionLabel>
      <View style={styles.row}>
        <View style={p.flex}><PickerField label={t('planner.hours.start')} pickerTitle={t('planner.hours.pickerStart')} mode="time" locale={dateLocale} text={draft.dayStart}
          value={dateFromLocalTime(draft.dayStart)} onChange={date => { update({ dayStart: vnLocalTime(date) }); setErrors(previous => ({ ...previous, hours: undefined })); }} /></View>
        <View style={p.flex}><PickerField label={t('planner.hours.end')} pickerTitle={t('planner.hours.pickerEnd')} mode="time" locale={dateLocale} text={draft.dayEnd}
          value={dateFromLocalTime(draft.dayEnd)} onChange={date => { update({ dayEnd: vnLocalTime(date) }); setErrors(previous => ({ ...previous, hours: undefined })); }} /></View>
      </View>
      <FieldError>{errors.hours}</FieldError>

      <SectionLabel>{t('planner.pace.label')}</SectionLabel>
      <Segmented<Pace> role="radio" label={t('planner.pace.label')} value={draft.pace} onChange={pace => update({ pace })}
        options={paces.map(pace => ({ label: t(`planner.pace.${pace}`), value: pace }))} />

      <SectionLabel hint={t('planner.interests.hint')}>{t('planner.interests.label')}</SectionLabel>
      {categories ? <ChipRow>{categories.map(category => {
        const checked = draft.interests.includes(category.code);
        return <Chip key={category.code} kind="checkbox" icon={categoryIcon(category.code)} label={vi ? category.name_vi : category.name_en} selected={checked}
          onPress={() => update({ interests: checked ? draft.interests.filter(code => code !== category.code) : [...draft.interests, category.code] })} />;
      })}</ChipRow> : <View accessible accessibilityLabel={t('planner.interests.loading')} style={styles.chipSkeletons}>
        {[96, 120, 88, 110].map((width, index) => <Skeleton key={index} width={width} height={46} radius={radii.chip} />)}
      </View>}

      <SectionLabel>{t('planner.modes.label')}</SectionLabel>
      <View style={styles.row}>{travelModes.map(mode => {
        const checked = draft.modes.includes(mode);
        return <Chip key={mode} grow kind="checkbox" icon={travelModeIcon(mode)} label={t(`planner.modes.${mode}`)} selected={checked}
          onPress={() => { update({ modes: checked ? draft.modes.filter(item => item !== mode) : [...draft.modes, mode] }); setErrors(previous => ({ ...previous, modes: undefined })); }} />;
      })}</View>
      <FieldError>{errors.modes}</FieldError>

      <SectionLabel trailing={draft.mustSee.length ? <Text style={styles.count}>{t('planner.mustSee.count', { count: draft.mustSee.length })}</Text> : undefined}>
        {t('planner.mustSee.label')}
      </SectionLabel>
      {draft.mustSee.length > 0 && <View style={styles.mustSeeList}>{draft.mustSee.map(place => <View key={place.id} style={styles.placeChip}>
        <Icon name="map-pin" size={16} color={colors.tealText} />
        <Text numberOfLines={1} style={styles.placeText}>{place.name}</Text>
        <Pressable accessibilityRole="button" accessibilityLabel={t('planner.mustSee.remove', { name: place.name })} hitSlop={6}
          onPress={() => update({ mustSee: draft.mustSee.filter(item => item.id !== place.id) })} style={({ pressed }) => [styles.remove, pressed && { opacity: 0.6 }]}>
          <Text aria-hidden style={styles.removeGlyph}>×</Text>
        </Pressable>
      </View>)}</View>}
      {city && <Pressable accessibilityRole="button" accessibilityLabel={t('planner.mustSee.add', { city: cityName(city) })} accessibilityState={{ disabled: mustSeeFull }}
        disabled={mustSeeFull} onPress={() => setPickerOpen(true)} style={({ pressed }) => [styles.addPlace, (pressed || mustSeeFull) && { opacity: 0.55 }]}>
        <View style={styles.addPlus}><Text aria-hidden style={styles.addPlusGlyph}>+</Text></View>
        <Text style={[p.link, p.flex]}>{t('planner.mustSee.add', { city: cityName(city) })}</Text>
        <Icon name="chevron-right" size={18} color={colors.textMuted} />
      </Pressable>}
      {mustSeeFull && <Text style={p.hint}>{t('planner.mustSee.max')}</Text>}
      {city && <MustSeePicker visible={pickerOpen} cityId={city.id} cityName={cityName(city)} selected={draft.mustSee} onChange={mustSee => update({ mustSee })} onClose={() => setPickerOpen(false)} />}
    </>}
  </PlannerShell>;
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', gap: spacing.sm },
  reason: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted, textAlign: 'center', marginBottom: spacing.xs },
  prefill: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.sm },
  prefillText: { fontFamily: fonts.medium, fontSize: 14, color: colors.tealText },
  credit: { fontFamily: fonts.medium, fontSize: 12, color: colors.textMuted, marginTop: spacing.xs },
  tileSkeletons: { flexDirection: 'row', gap: spacing.sm, paddingVertical: 6 },
  chipSkeletons: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  textArea: { minHeight: 168, borderWidth: 1, borderColor: tone.border, borderRadius: radii.card, backgroundColor: colors.white, paddingHorizontal: 18, paddingTop: 14, paddingBottom: 12 },
  textInput: { flex: 1, minHeight: 120, fontFamily: fonts.regular, fontSize: 17, lineHeight: 25, color: colors.ink, padding: 0 },
  counter: { alignSelf: 'flex-end', fontFamily: fonts.bold, fontSize: 13, color: colors.textMuted, marginTop: 6 },
  learnMore: { flexDirection: 'row', alignItems: 'center', gap: 2, minHeight: 44, alignSelf: 'flex-start' },
  understood: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.xs, marginTop: spacing.xl, backgroundColor: colors.surfaceTint, borderRadius: radii.field, padding: 14 },
  understoodText: { flex: 1, fontFamily: fonts.regular, fontSize: 15, lineHeight: 21, color: colors.deepOcean },
  secondary: { marginTop: spacing.xl },
  count: { fontFamily: fonts.bold, fontSize: 13, color: colors.ink, backgroundColor: colors.surfaceTint, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 4, overflow: 'hidden' },
  mustSeeList: { gap: spacing.xs, marginBottom: spacing.xs },
  placeChip: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 52, borderRadius: radii.field, backgroundColor: colors.surfaceTint, paddingLeft: 14, paddingRight: 4 },
  placeText: { flex: 1, fontFamily: fonts.bold, fontSize: 15, color: colors.ink },
  remove: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  removeGlyph: { fontSize: 24, lineHeight: 26, color: colors.deepOcean },
  addPlace: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, minHeight: 58, borderRadius: radii.field, borderWidth: 1.5, borderStyle: 'dashed', borderColor: colors.hairline, backgroundColor: colors.white, paddingLeft: 8, paddingRight: 14 },
  addPlus: { width: 40, height: 40, borderRadius: 13, backgroundColor: colors.surfaceTint, alignItems: 'center', justifyContent: 'center' },
  addPlusGlyph: { fontFamily: fonts.bold, fontSize: 22, lineHeight: 24, color: colors.tealText },
});
