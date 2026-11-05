import i18n from 'i18next';
import { getLocales } from 'expo-localization';
import * as SecureStore from 'expo-secure-store';
import { initReactI18next } from 'react-i18next';

import enAccount from './locales/en/account.json';
import enAuth from './locales/en/auth.json';
import enCommon from './locales/en/common.json';
import enExplore from './locales/en/explore.json';
import enGuide from './locales/en/guide.json';
import enHome from './locales/en/home.json';
import enHomeSheet from './locales/en/homeSheet.json';
import enOnboarding from './locales/en/onboarding.json';
import enPlace from './locales/en/place.json';
import enPlanner from './locales/en/planner.json';
import enProposal from './locales/en/proposal.json';
import enSave from './locales/en/save.json';
import enTabs from './locales/en/tabs.json';
import enTrips from './locales/en/trips.json';
import viAccount from './locales/vi/account.json';
import viAuth from './locales/vi/auth.json';
import viCommon from './locales/vi/common.json';
import viExplore from './locales/vi/explore.json';
import viGuide from './locales/vi/guide.json';
import viHome from './locales/vi/home.json';
import viHomeSheet from './locales/vi/homeSheet.json';
import viOnboarding from './locales/vi/onboarding.json';
import viPlace from './locales/vi/place.json';
import viPlanner from './locales/vi/planner.json';
import viProposal from './locales/vi/proposal.json';
import viSave from './locales/vi/save.json';
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
  explore: enExplore,
  guide: enGuide,
  home: enHome,
  homeSheet: enHomeSheet,
  onboarding: enOnboarding,
  place: enPlace,
  planner: enPlanner,
  proposal: enProposal,
  save: enSave,
  tabs: enTabs,
  trips: enTrips,
};

const vi: Record<keyof typeof en, object> = {
  account: viAccount,
  auth: viAuth,
  common: viCommon,
  explore: viExplore,
  guide: viGuide,
  home: viHome,
  homeSheet: viHomeSheet,
  onboarding: viOnboarding,
  place: viPlace,
  planner: viPlanner,
  proposal: viProposal,
  save: viSave,
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

/** SCR-039 language choice: an explicit locale, or follow the device. Stored on device only (no account sync yet). */
export type LanguageChoice = AppLocale | 'device';
const LANGUAGE_KEY = 'app.language';

/** Saved choice, or `device` when nothing (or something unknown) is stored or storage is unavailable (e.g. web). */
export async function loadLanguageChoice(): Promise<LanguageChoice> {
  try {
    const saved = await SecureStore.getItemAsync(LANGUAGE_KEY);
    return saved === 'vi' || saved === 'en' ? saved : 'device';
  } catch {
    return 'device';
  }
}

/** Applies the choice immediately, then persists it. The UI language changes even if storage fails. */
export async function setLanguageChoice(choice: LanguageChoice): Promise<void> {
  await i18n.changeLanguage(choice === 'device' ? deviceLocale() : choice);
  try {
    if (choice === 'device') await SecureStore.deleteItemAsync(LANGUAGE_KEY);
    else await SecureStore.setItemAsync(LANGUAGE_KEY, choice);
  } catch {
    // Storage unavailable: the choice holds for this session only.
  }
}

// Sync init above uses the device default; a saved choice is applied as soon as storage answers.
void loadLanguageChoice().then(choice => {
  if (choice !== 'device' && i18n.language !== choice) void i18n.changeLanguage(choice);
});

/** Locale for API calls (`Locale` parameter); follows the SCR-039 language setting. */
export function currentLocale(): AppLocale {
  return i18n.resolvedLanguage === 'vi' ? 'vi' : 'en';
}

export default i18n;
