import { useEffect, useMemo, useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { useAccount, type Interest } from '../../account/AccountContext';
import { currentLocale } from '../../../i18n';
import { ApiError, createTrip, getPreferences, listCategories, listCities } from '../../../lib/api/source';
import type { Category, CategoryCode, City, ClarificationRequired, IsoDate, Pace, PlanPreviewCreate, TravelMode, Uuid } from '../../../lib/api/types';
import { DEFAULT_CITY_CODE } from '../../../lib/api/types';
import { Icon, PrimaryButton, SecondaryButton, Skeleton, categoryIcon, normalizeCategoryCode, travelModeIcon } from '../../../components/ui';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { categoryColor, colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { errorCopy, toErrorDetail } from '../progress/errorCopy';
import { setPlanRequest } from '../progress/planRequestStore';
import {
  acknowledgeAiNotice, isAiNoticeAcknowledged, readDraft, rememberTrip, reusableTrip, takePendingView, tripShape, writeDraft, type InputMode,
  type PlannerDraft, type PlannerView,
} from './draftStore';
import { MUST_SEE_MAX, MustSeePicker } from './MustSeePicker';
import {
  Banner, Chip, ChipRow, CityTiles, FieldError, IntroCard, PickerField, PlannerShell, Segmented, SectionLabel, UserBubble, p, tone,
} from './PlannerUI';
import { addDays, RangeCalendar } from './RangeCalendar';
import { dateFromIso, dateFromLocalTime, dayMonthYear, minutesOf, todayVn, vnIsoDate, vnLocalTime, weekdayOf } from './vnTime';
import { DestinationCard, LinkRow, ReviewCard, StepProgress, StepTitle, WIZARD_STEPS, WizardFooter } from './WizardSteps';

const TEXT_MAX = 500;
const TITLE_MAX = 60;
/** "No early starts" preset (ui-research §3.2): the day starts at 09:30. */
const LATE_START = '09:30';
const DEFAULT_START = '08:30';
const COUNTER_FROM = 400;
const paces: Pace[] = ['RELAXED', 'BALANCED', 'PACKED'];
const travelModes: TravelMode[] = ['WALK', 'DRIVE'];
const dayCounts = [1, 2, 3] as const;
/** Saved profile interests (onboarding) → catalog category codes, used only when API-004 has none. */
const profileInterestCodes: Record<Interest, CategoryCode> = { Beach: 'BEACH', Culture: 'HERITAGE', Food: 'FOOD', Nature: 'NATURE' };

const emptyDraft = (): PlannerDraft => ({
  cityId: null, dayCount: null, dayEnd: '18:00', dayStart: '08:30', interests: [], mode: 'form', modes: ['WALK'], mustSee: [],
  pace: 'BALANCED', prefilled: false, requestText: '', startDate: null, title: '',
});

type WeekdayIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6;

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
  /** Wizard step 1–4 (When · Style · Must-sees & notes · Review). Kept while this screen is open. */
  const [step, setStep] = useState(1);

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
        // Older servers/drafts used lower-case codes; the API now returns UPPER_CASE (e.g. HERITAGE).
        const saved = prefs.interest_category_codes.map(code => normalizeCategoryCode(code) ?? code);
        const interests = saved.length ? saved : fromProfile;
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
      // Wizard: go back to the step that holds the first invalid field.
      else setStep(fieldErrors.startDate || fieldErrors.dayCount ? 1 : 2);
      return;
    }
    if (draft.requestText.trim() && !noticeAcked) { acknowledgeAiNotice(); setNoticeAcked(true); }
    setBusy(true);
    try {
      const title = draft.title?.trim() ? draft.title.trim().slice(0, TITLE_MAX) : null;
      // Same city, start date and day count as the last submit: plan on that DRAFT trip again (no new trip per submit).
      const shape = tripShape(city.id, draft.startDate, draft.dayCount);
      const trip = reusableTrip(shape) ?? await createTrip({ city_id: city.id, day_count: draft.dayCount, start_date: draft.startDate, title });
      rememberTrip(trip, shape);
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
      if (detail.code === 'validation_error' && error instanceof ApiError) {
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

  /* ------------------------------------------------------------------ Describe view (free text) */
  const describing = draft.mode === 'describe';
  const mustSeeFull = draft.mustSee.length >= MUST_SEE_MAX;
  const noticeBanner = !noticeAcked && <View style={{ marginTop: spacing.lg }}>
    <Banner tone="info" title={t('planner.notice.title')}
      action={<Pressable accessibilityRole="link" accessibilityLabel={t('planner.notice.learnMore')} onPress={() => router.push('/settings')} style={styles.learnMore}>
        <Text style={p.link}>{t('planner.notice.learnMore')}</Text>
        <Icon name="chevron-right" size={16} color={colors.tealText} />
      </Pressable>}>
      {t('planner.notice.body')}
    </Banner>
  </View>;

  const textArea = (label: string, placeholder: string, hint?: string) => <>
    <View style={[styles.textArea, !!errors.text && p.invalid]}>
      <TextInput multiline value={draft.requestText} maxLength={TEXT_MAX} accessibilityLabel={label} accessibilityHint={hint}
        placeholder={placeholder} placeholderTextColor={colors.textMuted} textAlignVertical="top" style={styles.textInput}
        onChangeText={requestText => { update({ requestText }); if (errors.text) setErrors({}); }} />
      {textLength >= COUNTER_FROM && <Text accessibilityLiveRegion="polite" style={[styles.counter, textLength >= TEXT_MAX && { color: tone.error }]}>{t('planner.describe.counter', { count: textLength })}</Text>}
    </View>
    {hint ? <Text style={p.hint}>{hint}</Text> : null}
  </>;

  if (describing) {
    const emptyText = !draft.requestText.trim();
    return <PlannerShell title={t('planner.title')}
      footer={<>
        {emptyText && <Text style={styles.reason}>{t('planner.validation.text')}</Text>}
        {!!submitError && <Text accessibilityRole="alert" style={[styles.reason, { color: tone.error }]}>{submitError}</Text>}
        <PrimaryButton label={busy ? t('planner.submit.creating') : t('planner.submit.continue')} loading={busy} disabled={!city || emptyText}
          accessibilityHint={emptyText ? t('planner.validation.text') : undefined} onPress={() => void submit()} />
      </>}>
      <IntroCard label={t('planner.intro.label')} body={t('planner.intro.body')} />
      <LinkRow icon="back" label={t('planner.wizard.useForm')} onPress={() => { update({ mode: 'form' }); setErrors({}); setSubmitError(null); setStep(1); }} />
      <SectionLabel>{t('planner.describe.prompt')}</SectionLabel>
      {textArea(t('planner.describe.label'), t('planner.describe.placeholder'), t('planner.describe.hint'))}
      <FieldError>{errors.text}</FieldError>
      {noticeBanner}
    </PlannerShell>;
  }

  /* ------------------------------------------------------------------ Create-trip wizard (SCR-022, 4 steps) */
  const shortDate = (date: IsoDate) => `${t(`planner.weekday.${weekdayOf(date) as WeekdayIndex}`)} ${dayMonthYear(date).slice(0, 5)}`;
  const endDate = draft.startDate && draft.dayCount ? addDays(draft.startDate, draft.dayCount - 1) : null;
  const rangeText = draft.startDate && draft.dayCount && endDate
    ? t('planner.wizard.when.range', { count: draft.dayCount, end: shortDate(endDate), start: shortDate(draft.startDate) })
    : null;
  const lateStart = draft.dayStart === LATE_START;
  const modeNames = draft.modes.map(mode => t(`planner.modes.${mode}`)).join(', ');

  function leave() {
    if (router.canGoBack()) router.back();
    else router.replace('/home');
  }

  function back() {
    setSubmitError(null);
    if (step > 1) { setStep(step - 1); return; }
    Alert.alert(t('planner.wizard.exit.title'), t('planner.wizard.exit.body'), [
      { style: 'cancel', text: t('planner.wizard.exit.stay') },
      { onPress: leave, style: 'destructive', text: t('planner.wizard.exit.leave') },
    ]);
  }

  function next() {
    setSubmitError(null);
    const fieldErrors = validateForm();
    if (step === 1) {
      const stepErrors = { dayCount: fieldErrors.dayCount, startDate: fieldErrors.startDate };
      setErrors(previous => ({ ...previous, ...stepErrors }));
      if (stepErrors.startDate || stepErrors.dayCount) return;
    }
    if (step === 2) {
      const stepErrors = { hours: fieldErrors.hours, modes: fieldErrors.modes };
      setErrors(previous => ({ ...previous, ...stepErrors }));
      if (stepErrors.hours || stepErrors.modes) return;
    }
    if (step < WIZARD_STEPS) { setStep(step + 1); return; }
    void submit();
  }

  const stepReason = step === 1 && !draft.startDate ? t('planner.validation.startDate') : null;
  const lastStep = step === WIZARD_STEPS;
  const editHint = t('planner.wizard.review.editHint');

  return <PlannerShell title={t('planner.wizard.title')} onBack={back} scrollKey={step}
    subheader={<StepProgress current={step} />}
    footer={<WizardFooter
      disabled={!city || (step === 1 && !draft.startDate)}
      error={submitError}
      loading={busy && lastStep}
      nextIcon={lastStep ? 'sparkle' : undefined}
      nextLabel={lastStep ? (busy ? t('planner.submit.creating') : t('planner.submit.create')) : t('planner.wizard.next')}
      onBack={back}
      onNext={next}
      reason={stepReason}
      step={step}
    />}>
    {step === 1 && <>
      <StepTitle hint={t('planner.wizard.when.hint')}>{t('planner.wizard.when.title')}</StepTitle>
      {prefillShown && <View style={styles.prefill}>
        <Icon name="check" size={16} color={colors.tealText} strokeWidth={2.4} />
        <Text style={styles.prefillText}>{t('planner.prefilled')}</Text>
      </View>}
      {cities && cities.length > 1 ? cityPicker(item => setCity(item.id), draft.cityId) : null}
      {city
        ? <DestinationCard
          credit={credit ? t('planner.city.photoCredit', { credit }) : null}
          image={CITY_IMAGES[city.code] ?? null}
          name={cityName(city)}
          subtitle={city.code === DEFAULT_CITY_CODE ? t('planner.wizard.when.destinationSub') : t('planner.wizard.when.destinationOther')}
        />
        : <View style={styles.destinationSkeleton}><Skeleton height={140} radius={radii.photoCard} /></View>}
      <RangeCalendar
        dayCount={draft.dayCount}
        onChange={({ startDate, dayCount }) => { update({ dayCount, startDate }); setErrors(previous => ({ ...previous, dayCount: undefined, startDate: undefined })); }}
        onTooLong={() => setErrors(previous => ({ ...previous, startDate: t('planner.wizard.when.max') }))}
        startDate={draft.startDate}
        today={today}
      />
      {rangeText ? <View accessibilityLiveRegion="polite" style={styles.range}>
        <Icon name="calendar" size={18} color={colors.tealText} />
        <Text style={styles.rangeText}>{rangeText}</Text>
      </View> : null}
      <FieldError>{errors.startDate ?? errors.dayCount}</FieldError>
      <LinkRow label={t('planner.wizard.when.describe')} onPress={() => { update({ mode: 'describe' }); setErrors({}); setSubmitError(null); }} />
    </>}

    {step === 2 && <>
      <StepTitle hint={t('planner.wizard.style.hint')}>{t('planner.wizard.style.title')}</StepTitle>
      <SectionLabel>{t('planner.pace.label')}</SectionLabel>
      <View accessibilityRole="radiogroup" accessibilityLabel={t('planner.pace.label')} style={styles.row}>
        {paces.map(pace => <Chip key={pace} grow kind="radio" label={t(`planner.pace.${pace}`)} selected={draft.pace === pace} onPress={() => update({ pace })} />)}
      </View>

      <SectionLabel>{t('planner.interests.label')}</SectionLabel>
      {categories ? <ChipRow>{categories.map(category => {
        const checked = draft.interests.includes(category.code);
        return <Chip key={category.code} kind="checkbox" icon={categoryIcon(category.code)} label={vi ? category.name_vi : category.name_en} selected={checked} tone={categoryColor(category.code)}
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

      <SectionLabel>{t('planner.hours.label')}</SectionLabel>
      <ChipRow>
        <Chip kind="checkbox" icon="clock" label={t('planner.wizard.style.noEarly')} selected={lateStart}
          onPress={() => { update({ dayStart: lateStart ? DEFAULT_START : LATE_START }); setErrors(previous => ({ ...previous, hours: undefined })); }} />
      </ChipRow>
      <View style={[styles.row, styles.hours]}>
        <View style={p.flex}><PickerField label={t('planner.hours.start')} pickerTitle={t('planner.hours.pickerStart')} mode="time" locale={dateLocale} text={draft.dayStart}
          value={dateFromLocalTime(draft.dayStart)} onChange={date => { update({ dayStart: vnLocalTime(date) }); setErrors(previous => ({ ...previous, hours: undefined })); }} /></View>
        <View style={p.flex}><PickerField label={t('planner.hours.end')} pickerTitle={t('planner.hours.pickerEnd')} mode="time" locale={dateLocale} text={draft.dayEnd}
          value={dateFromLocalTime(draft.dayEnd)} onChange={date => { update({ dayEnd: vnLocalTime(date) }); setErrors(previous => ({ ...previous, hours: undefined })); }} /></View>
      </View>
      <FieldError>{errors.hours}</FieldError>
    </>}

    {step === 3 && <>
      <StepTitle>{t('planner.wizard.notes.title')}</StepTitle>
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

      <SectionLabel hint={t('planner.wizard.notes.hint')}>{t('planner.wizard.notes.label')}</SectionLabel>
      {textArea(t('planner.wizard.notes.label'), t('planner.wizard.notes.placeholder'))}
      {draft.requestText.trim() ? noticeBanner : null}
    </>}

    {step === 4 && <>
      <StepTitle hint={t('planner.wizard.review.hint')}>{t('planner.wizard.review.title')}</StepTitle>
      <Text style={styles.nameLabel}>{t('planner.wizard.review.name')}</Text>
      <TextInput accessibilityLabel={t('planner.wizard.review.name')} maxLength={TITLE_MAX} onChangeText={title => update({ title })}
        placeholder={t('planner.wizard.review.namePlaceholder', { city: cityName(city), count: draft.dayCount ?? 1 })} placeholderTextColor={colors.textMuted}
        returnKeyType="done" style={styles.nameInput} value={draft.title ?? ''} />
      <View style={styles.reviewList}>
        <ReviewCard editLabel={editHint} icon="calendar" onPress={() => setStep(1)} title={t('planner.wizard.review.when')}
          lines={[cityName(city), rangeText ?? t('planner.validation.startDate')].filter(Boolean)} />
        <ReviewCard editLabel={editHint} icon="sliders" onPress={() => setStep(2)} title={t('planner.wizard.review.style')}
          lines={[
            [t(`planner.pace.${draft.pace}`), modeNames].filter(Boolean).join(' · '),
            interestNames.length ? interestNames.join(', ') : t('planner.wizard.review.noInterests'),
            t('planner.wizard.review.hours', { end: draft.dayEnd, start: draft.dayStart }),
          ]} />
        <ReviewCard editLabel={editHint} icon="map-pin" onPress={() => setStep(3)} title={t('planner.wizard.review.notes')}
          lines={[
            draft.mustSee.length ? draft.mustSee.map(place => place.name).join(', ') : t('planner.wizard.review.noMustSees'),
            draft.requestText.trim() ? t('planner.wizard.review.note', { note: draft.requestText.trim() }) : t('planner.wizard.review.noNote'),
          ]} />
      </View>
    </>}
  </PlannerShell>;
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', gap: spacing.sm },
  hours: { marginTop: spacing.sm },
  range: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, marginTop: spacing.sm, padding: spacing.sm, borderRadius: radii.field, backgroundColor: colors.primarySoft },
  rangeText: { flex: 1, fontFamily: fonts.semibold, fontSize: 15, lineHeight: 20, color: colors.ink },
  nameInput: { minHeight: 52, borderWidth: 1, borderColor: tone.border, borderRadius: radii.field, backgroundColor: colors.white, paddingHorizontal: spacing.md, fontFamily: fonts.bold, fontSize: 16, color: colors.ink },
  reviewList: { marginTop: spacing.lg },
  destinationSkeleton: { marginBottom: spacing.md },
  nameLabel: { fontFamily: fonts.bold, fontSize: 14, color: colors.deepOcean, marginBottom: spacing.xs },
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
