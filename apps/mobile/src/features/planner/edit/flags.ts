import { useFixtures } from '../../../lib/api/source';

/** `FEATURE_REGENERATION` (S-5, cut 4th): hides Lock/Unlock, the lock badge and SCR-030 when off. */
export const regenerationEnabled = process.env.EXPO_PUBLIC_FEATURE_REGENERATION === '1';

/** Dev-only fixture controls (simulate a failure on the next edit). Never shown in a release build. */
export const showFixtureControls = __DEV__ && useFixtures;

/** SCR-027 duration stepper (ASM-061): 15-minute steps within 15–240 min. */
export const VISIT_STEP = 15;
export const VISIT_MIN = 15;
export const VISIT_MAX = 240;
