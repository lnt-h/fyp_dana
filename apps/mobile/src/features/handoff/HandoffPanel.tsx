import * as WebBrowser from 'expo-web-browser';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AccessibilityInfo, Linking, Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, Skeleton } from '../../components/ui';
import { ApiError, getTrip, listCities } from '../../lib/api/source';
import { getHandoffLinks, getStayPrices, stayPricesEnabled, type StayPrice, type StayPricePage } from '../../lib/api/sourceTrips';
import type { City, HandoffKind, HandoffLink, TripDetail, Uuid } from '../../lib/api/types';
import { colors } from '../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { useIsOffline } from '../home/useNetwork';
import { addIsoDays, cityName, formatShortDate } from '../save/format';
import { HandoffIcon } from './kindIcons';

const border = colors.hairline;
const errorText = colors.danger;
const ALL_KINDS: HandoffKind[] = ['STAY', 'ACTIVITY', 'TRANSPORT'];

export type HandoffPanelProps = {
  tripId: Uuid;
  /** Which partner groups to show (default all three: Agoda + Booking.com, Klook, 12Go). */
  kinds?: HandoffKind[];
  /** ACTIVITY is scoped to a saved stop (API-030 `stop_id`); defaults to the trip's first stop. */
  stopId?: Uuid;
  /** Shows a back chevron in the header (e.g. when the panel replaces the Save success view in the same sheet). */
  onBack?: () => void;
};

type Load =
  | { state: 'loading' }
  | { state: 'error'; code: string }
  | { state: 'ready'; trip: TripDetail; city: City | null; links: HandoffLink[] };

type Prices = { state: 'off' } | { state: 'loading' } | { state: 'unavailable' } | { state: 'ready'; page: StayPricePage };

/** Wall-clock HH:MM in Asia/Ho_Chi_Minh for a retrieval timestamp. */
function vnTime(iso: string): string {
  const local = new Date(new Date(iso).getTime() + 7 * 3_600_000);
  return `${String(local.getUTCHours()).padStart(2, '0')}:${String(local.getUTCMinutes()).padStart(2, '0')}`;
}

function formatMoney(amount: string, currency: string, isVi: boolean): string {
  const value = Number(amount);
  try {
    return new Intl.NumberFormat(isVi ? 'vi-VN' : 'en-US', { currency, maximumFractionDigits: 0, style: 'currency' }).format(value);
  } catch {
    return `${amount} ${currency}`;
  }
}

/** Opens a partner URL in the system browser; falls back to an in-app browser tab. Returns false when neither works. */
async function openExternal(url: string): Promise<boolean> {
  try {
    await Linking.openURL(url);
    return true;
  } catch {
    try {
      await WebBrowser.openBrowserAsync(url);
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * SCR-037 Booking handoff content: partner deep links prefilled with the saved trip's city and dates, plus (behind
 * FEATURE_STAY_PRICES) indicative stay prices that are shown once and never cached or stored. Gonarra never books or
 * takes payment; every row leaves the app.
 */
export function HandoffPanel({ tripId, kinds = ALL_KINDS, stopId, onBack }: HandoffPanelProps) {
  const { t, i18n } = useTranslation();
  const isVi = i18n.resolvedLanguage === 'vi';
  const offline = useIsOffline();
  const [load, setLoad] = useState<Load>({ state: 'loading' });
  const [prices, setPrices] = useState<Prices>({ state: 'off' });
  const [attempt, setAttempt] = useState(0);
  const [notice, setNotice] = useState('');
  const kindsKey = kinds.join(',');
  const wantsPrices = stayPricesEnabled && kinds.includes('STAY');

  useEffect(() => {
    let active = true;
    setLoad({ state: 'loading' });
    const requested = kindsKey.split(',') as HandoffKind[];
    Promise.all([getTrip(tripId), listCities().catch(() => [] as City[])])
      .then(async ([trip, cities]) => {
        const firstStop = trip.days[0]?.stops[0]?.id;
        const links = await getHandoffLinks(tripId, { kinds: requested, stopId: stopId ?? firstStop });
        if (active) setLoad({ city: cities.find(item => item.id === trip.city_id) ?? null, links, state: 'ready', trip });
      })
      .catch((error: unknown) => {
        if (active) setLoad({ code: error instanceof ApiError ? error.error.code : 'network', state: 'error' });
      });
    return () => { active = false; };
  }, [tripId, kindsKey, stopId, attempt]);

  useEffect(() => {
    if (!wantsPrices) { setPrices({ state: 'off' }); return; }
    let active = true;
    setPrices({ state: 'loading' });
    // Runtime only: the page lives in this component's state and is dropped on unmount (FR-081, no-store).
    getStayPrices(tripId)
      .then(page => { if (active) setPrices(page.items.length ? { page, state: 'ready' } : { state: 'unavailable' }); })
      .catch(() => { if (active) setPrices({ state: 'unavailable' }); });
    return () => { active = false; };
  }, [tripId, wantsPrices, attempt]);

  const open = useCallback(async (url: string, partner: string) => {
    setNotice('');
    const ok = await openExternal(url);
    if (!ok) {
      const message = t('save.handoff.openError', { partner });
      setNotice(message);
      AccessibilityInfo.announceForAccessibility(message);
    }
  }, [t]);

  const city = load.state === 'ready' ? cityName(load.city, isVi) : '';
  const singleKind = kinds.length === 1 ? kinds[0] : null;
  const title = singleKind === 'STAY'
    ? t('save.handoff.titleStay', { city })
    : singleKind === 'ACTIVITY'
      ? t('save.handoff.titleActivity', { city })
      : singleKind === 'TRANSPORT'
        ? t('save.handoff.titleTransport', { city })
        : t('save.handoff.title');

  const prefill = useMemo(() => {
    if (load.state !== 'ready') return null;
    const { trip } = load;
    const start = formatShortDate(t, trip.start_date);
    const end = formatShortDate(t, addIsoDays(trip.start_date, trip.day_count));
    const stop = trip.days.flatMap(day => day.stops).find(item => item.id === stopId) ?? trip.days[0]?.stops[0];
    return {
      ACTIVITY: stop ? t('save.handoff.prefillActivity', { stop: stop.name }) : t('save.handoff.prefillActivityCity', { city }),
      STAY: t('save.handoff.prefillStay', { count: trip.day_count, end, start }),
      TRANSPORT: t('save.handoff.prefillTransport', { start }),
    } satisfies Record<HandoffKind, string>;
  }, [city, load, stopId, t]);

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        {onBack ? (
          <Pressable accessibilityLabel={t('save.handoff.back')} accessibilityRole="button" hitSlop={4} onPress={onBack} style={({ pressed }) => [styles.back, pressed && styles.pressed]}>
            <Icon name="back" size={22} />
          </Pressable>
        ) : null}
        <View style={styles.headerText}>
          {load.state === 'ready' ? (
            <View style={styles.contextRow}>
              <Text style={styles.context}>{t('save.handoff.context', { city, count: load.trip.day_count })}</Text>
              <View style={styles.savedBadge}>
                <Icon color={colors.tealText} name="check" size={14} strokeWidth={2.4} />
                <Text style={styles.savedText}>{t('save.handoff.saved')}</Text>
              </View>
            </View>
          ) : null}
          <Text accessibilityRole="header" style={styles.title}>{title}</Text>
        </View>
      </View>

      {offline ? (
        <View accessibilityRole="alert" style={styles.offline}>
          <Icon color={colors.tealText} name="info" size={20} />
          <Text style={styles.offlineText}>{t('save.handoff.offline')}</Text>
        </View>
      ) : null}

      {load.state === 'loading' ? (
        <View accessibilityLabel={t('save.handoff.loading')} accessibilityRole="progressbar" style={styles.list}>
          <Skeleton height={76} radius={radii.card} />
          <Skeleton height={76} radius={radii.card} />
        </View>
      ) : null}

      {load.state === 'error' ? (
        <EmptyCard
          body={load.code === 'trip_not_saved' ? t('save.handoff.notSaved') : t('save.handoff.error')}
          onRetry={load.code === 'trip_not_saved' ? undefined : () => setAttempt(n => n + 1)}
          retryLabel={t('save.handoff.retry')}
          title={t('save.handoff.emptyTitle')}
        />
      ) : null}

      {load.state === 'ready' && load.links.length === 0 ? (
        <EmptyCard body={t('save.handoff.emptyBody')} onRetry={() => setAttempt(n => n + 1)} retryLabel={t('save.handoff.retry')} title={t('save.handoff.emptyTitle')} />
      ) : null}

      {load.state === 'ready' && prefill
        ? kinds.map(kind => {
          const links = load.links.filter(link => link.kind === kind);
          if (!links.length) return null;
          return (
            <View key={kind} style={styles.group}>
              {singleKind ? null : <Text accessibilityRole="header" style={styles.cap}>{t(`save.handoff.section.${kind}`)}</Text>}
              <View style={styles.prefill}>
                <Icon color={colors.tealText} name="calendar" size={16} />
                <Text style={styles.prefillText}>{prefill[kind]}</Text>
              </View>
              <View style={styles.list}>
                {links.map(link => (
                  <PartnerRow
                    disabled={offline}
                    key={link.partner_key}
                    link={link}
                    onPress={() => void open(link.url, link.partner_display_name)}
                    subtitle={offline ? t('save.handoff.offline') : t(`save.handoff.partnerSub.${kind}`, { city })}
                  />
                ))}
              </View>
              {kind === 'STAY' && prices.state !== 'off' ? (
                <PriceSection disabled={offline} isVi={isVi} onOpen={open} prices={prices} />
              ) : null}
            </View>
          );
        })
        : null}

      {notice ? <Text accessibilityLiveRegion="polite" style={styles.notice}>{notice}</Text> : null}

      <View style={styles.disclosure}>
        <Icon color={colors.textMuted} name="info" size={18} />
        <Text style={styles.disclosureText}>{t('save.handoff.leave')}</Text>
      </View>
    </View>
  );
}

function PartnerRow({ link, subtitle, disabled, onPress }: { link: HandoffLink; subtitle: string; disabled: boolean; onPress: () => void }) {
  const { t } = useTranslation();
  return (
    <Pressable
      accessibilityHint={t('save.handoff.opensExternal')}
      accessibilityLabel={t('save.handoff.partnerLabel', { partner: link.partner_display_name, subtitle })}
      accessibilityRole="link"
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [styles.row, disabled && styles.disabled, pressed && styles.rowPressed]}
    >
      <View style={styles.tile}>
        <HandoffIcon color={colors.deepOcean} name={link.kind} />
      </View>
      <View style={styles.rowText}>
        <Text numberOfLines={1} style={styles.partner}>{link.partner_display_name}</Text>
        <Text numberOfLines={2} style={styles.rowSub}>{subtitle}</Text>
      </View>
      <View style={styles.arrow}>
        <HandoffIcon color={colors.tealText} name="external" size={20} />
      </View>
    </Pressable>
  );
}

function PriceSection({ prices, isVi, disabled, onOpen }: { prices: Exclude<Prices, { state: 'off' }>; isVi: boolean; disabled: boolean; onOpen: (url: string, partner: string) => Promise<void> }) {
  const { t } = useTranslation();
  if (prices.state === 'loading') {
    return (
      <View accessibilityLabel={t('save.handoff.prices.loading')} accessibilityRole="progressbar" style={styles.priceCard}>
        <Skeleton height={14} width="40%" />
        <Skeleton height={44} />
        <Skeleton height={44} />
      </View>
    );
  }
  if (prices.state === 'unavailable') {
    return (
      <View style={styles.priceUnavailable}>
        <Icon color={colors.textMuted} name="info" size={18} />
        <Text style={styles.disclosureText}>{t('save.handoff.prices.unavailable')}</Text>
      </View>
    );
  }
  const { page } = prices;
  const label = (item: StayPrice) => {
    const price = formatMoney(item.price.amount, item.price.currency, isVi);
    return item.price_basis === 'TOTAL_STAY' ? t('save.handoff.prices.total', { price }) : t('save.handoff.prices.perNight', { price });
  };
  return (
    <View style={styles.priceCard}>
      <View style={styles.priceHead}>
        <Text accessibilityRole="header" style={styles.cap}>{t('save.handoff.prices.cap')}</Text>
        <View style={styles.priceTag}>
          <Text style={styles.priceTagText}>{t('save.handoff.prices.tag')}</Text>
        </View>
      </View>
      {page.items.slice(0, 10).map((item, index) => {
        const text = label(item);
        const words = item.price.currency === 'VND' ? t('save.handoff.prices.currencyVND') : item.price.currency;
        const url = item.handoff_url;
        return (
          <Pressable
            accessibilityLabel={t('save.handoff.prices.rowLabel', { currencyWords: words, name: item.name, price: text })}
            accessibilityRole={url ? 'link' : 'text'}
            disabled={!url || disabled}
            key={`${item.name}-${index}`}
            onPress={url ? () => void onOpen(url, item.name) : undefined}
            style={({ pressed }) => [styles.priceRow, index > 0 && styles.priceDivider, pressed && styles.pressed]}
          >
            <Text numberOfLines={2} style={styles.priceName}>{item.name}</Text>
            <Text style={styles.priceValue}>{text}</Text>
            {url ? <HandoffIcon color={colors.tealText} name="external" size={18} /> : null}
          </Pressable>
        );
      })}
      <Text style={styles.priceNotice}>{t('save.handoff.prices.notice', { time: vnTime(page.retrieved_at) })}</Text>
      <Text style={styles.priceAttribution}>{page.attribution_text}</Text>
    </View>
  );
}

function EmptyCard({ title, body, retryLabel, onRetry }: { title: string; body: string; retryLabel: string; onRetry?: () => void }) {
  return (
    <View accessibilityRole="alert" style={styles.empty}>
      <View style={styles.emptyIcon}>
        <Icon color={errorText} name="info" size={22} />
      </View>
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyBody}>{body}</Text>
      {onRetry ? (
        <Pressable accessibilityRole="button" hitSlop={4} onPress={onRetry} style={({ pressed }) => [styles.retry, pressed && styles.pressed]}>
          <Text style={styles.retryText}>{retryLabel}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  arrow: { alignItems: 'center', height: MIN_TOUCH, justifyContent: 'center', width: 32 },
  back: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: MIN_TOUCH / 2, height: MIN_TOUCH, justifyContent: 'center', width: MIN_TOUCH },
  cap: { color: colors.textMuted, fontFamily: fonts.bold, fontSize: 12, letterSpacing: 1.2, textTransform: 'uppercase' },
  context: { color: colors.textMuted, fontFamily: fonts.bold, fontSize: 14 },
  contextRow: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: 4 },
  disabled: { opacity: 0.5 },
  disclosure: { alignItems: 'flex-start', flexDirection: 'row', gap: spacing.xs, paddingTop: spacing.xs },
  disclosureText: { color: colors.textMuted, flex: 1, fontFamily: fonts.regular, fontSize: 13, lineHeight: 19 },
  empty: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: radii.card, gap: spacing.xs, padding: spacing.xl },
  emptyBody: { ...typography.body, color: colors.textMuted, fontSize: 15, lineHeight: 21, textAlign: 'center' },
  emptyIcon: { alignItems: 'center', backgroundColor: colors.dangerBg, borderRadius: radii.iconTile, height: 44, justifyContent: 'center', marginBottom: 4, width: 44 },
  emptyTitle: { ...typography.bodyStrong, textAlign: 'center' },
  group: { gap: spacing.sm },
  header: { alignItems: 'flex-start', flexDirection: 'row', gap: spacing.sm },
  headerText: { flex: 1 },
  list: { gap: spacing.sm },
  notice: { color: errorText, fontFamily: fonts.regular, fontSize: 14, lineHeight: 20 },
  offline: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: radii.inset, flexDirection: 'row', gap: spacing.sm, padding: spacing.sm },
  offlineText: { color: colors.ink, flex: 1, fontFamily: fonts.bold, fontSize: 14 },
  partner: { ...typography.bodyStrong, fontSize: 17 },
  prefill: { alignItems: 'center', alignSelf: 'flex-start', backgroundColor: colors.surfaceTint, borderRadius: radii.pill, flexDirection: 'row', gap: 6, paddingHorizontal: spacing.sm, paddingVertical: 6 },
  prefillText: { color: colors.ink, flexShrink: 1, fontFamily: fonts.bold, fontSize: 13, lineHeight: 18 },
  pressed: { opacity: 0.7 },
  priceAttribution: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 12, lineHeight: 16 },
  priceCard: { backgroundColor: colors.warnBg, borderColor: '#F3E2C2', borderRadius: radii.card, borderWidth: 1, gap: spacing.xs, padding: spacing.md },
  priceDivider: { borderTopColor: '#F3E2C2', borderTopWidth: StyleSheet.hairlineWidth },
  priceHead: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, justifyContent: 'space-between' },
  priceName: { ...typography.label, flex: 1 },
  priceNotice: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, marginTop: 4 },
  priceRow: { alignItems: 'center', flexDirection: 'row', gap: spacing.xs, minHeight: MIN_TOUCH, paddingVertical: 6 },
  priceTag: { backgroundColor: colors.white, borderRadius: radii.pill, paddingHorizontal: 10, paddingVertical: 4 },
  priceTagText: { color: colors.warn, fontFamily: fonts.bold, fontSize: 12 },
  priceUnavailable: { alignItems: 'center', flexDirection: 'row', gap: spacing.xs },
  priceValue: { color: colors.ink, fontFamily: fonts.bold, fontSize: 14 },
  retry: { alignItems: 'center', justifyContent: 'center', minHeight: MIN_TOUCH, paddingHorizontal: spacing.md },
  /** Ink + underline on the warm tint card (teal would be 4.45:1). */
  retryText: { color: colors.ink, fontFamily: fonts.bold, fontSize: 15, textDecorationLine: 'underline' },
  root: { gap: spacing.md },
  row: { alignItems: 'center', backgroundColor: colors.white, borderColor: border, borderRadius: radii.card, borderWidth: 1, flexDirection: 'row', gap: spacing.sm, minHeight: 76, paddingLeft: spacing.sm, paddingRight: spacing.xs, paddingVertical: spacing.sm },
  rowPressed: { backgroundColor: colors.surfaceTint },
  rowSub: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 14, lineHeight: 19 },
  rowText: { flex: 1 },
  savedBadge: { alignItems: 'center', backgroundColor: colors.okBg, borderRadius: radii.pill, flexDirection: 'row', gap: 4, paddingHorizontal: 8, paddingVertical: 2 },
  savedText: { color: colors.ok, fontFamily: fonts.bold, fontSize: 12 },
  tile: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: radii.iconTile, height: 48, justifyContent: 'center', width: 48 },
  title: { ...typography.headline, fontSize: 24, lineHeight: 30 },
});
