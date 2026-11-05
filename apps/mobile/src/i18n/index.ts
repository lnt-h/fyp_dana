import i18n from 'i18next';
import { getLocales } from 'expo-localization';
import { initReactI18next } from 'react-i18next';

import enAccount from './locales/en/account.json';
import enAuth from './locales/en/auth.json';
import enCommon from './locales/en/common.json';
import enGuide from './locales/en/guide.json';
import enHome from './locales/en/home.json';
import enOnboarding from './locales/en/onboarding.json';
import enPlace from './locales/en/place.json';
import enPlanner from './locales/en/planner.json';
import enProposal from './locales/en/proposal.json';
import enTabs from './locales/en/tabs.json';
import enTrips from './locales/en/trips.json';
import viAccount from './locales/vi/account.json';
import viAuth from './locales/vi/auth.json';
import viCommon from './locales/vi/common.json';
import viGuide from './locales/vi/guide.json';
import viHome from './locales/vi/home.json';
import viOnboarding from './locales/vi/onboarding.json';
import viPlace from './locales/vi/place.json';
import viPlanner from './locales/vi/planner.json';
import viProposal from './locales/vi/proposal.json';
import viTabs from './locales/vi/tabs.json';
import viTrips from './locales/vi/trips.json';

/** Contract `Locale` (openapi.yaml): the value sent to the API as `locale`. */
export type AppLocale = 'vi' | 'en';

/**
 * One JSON file per feature and language (`locales/{vi,en}/{feature}.json`), merged under the feature name so keys
 * read `feature.key` (e.g. `auth.login.title`). Add a feature by adding both files and one line to each map below.
 */
const en = {
  account: enAccount,
  auth: enAuth,
  common: enCommon,
  guide: enGuide,
  home: enHome,
  onboarding: enOnboarding,
  place: enPlace,
  planner: enPlanner,
  proposal: enProposal,
  tabs: enTabs,
  trips: enTrips,
};

const vi: Record<keyof typeof en, object> = {
  account: viAccount,
  auth: viAuth,
  common: viCommon,
  guide: viGuide,
  home: viHome,
  onboarding: viOnboarding,
  place: viPlace,
  planner: viPlanner,
  proposal: viProposal,
  tabs: viTabs,
  trips: viTrips,
};

/** English resource shape; drives typed `t()` keys (see i18next.d.ts). */
export type TranslationResource = typeof en;

export const resources = {
  en: { translation: en },
  vi: { translation: vi },
} as const;

/** Device default: Vietnamese when the first preferred locale is Vietnamese, otherwise English. */
export function deviceLocale(): AppLocale {
  return getLocales()[0]?.languageCode === 'vi' ? 'vi' : 'en';
}

void i18n.use(initReactI18next).init({
  fallbackLng: 'en',
  initAsync: false,
  interpolation: { escapeValue: false },
  lng: deviceLocale(),
  resources,
  returnNull: false,
  supportedLngs: ['vi', 'en'],
});

/** Locale for API calls (`Locale` parameter); a language setting (SCR-039, TASK-012) can override it later. */
export function currentLocale(): AppLocale {
  return i18n.resolvedLanguage === 'vi' ? 'vi' : 'en';
}

export default i18n;
