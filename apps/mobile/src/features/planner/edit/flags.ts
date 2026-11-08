/** `FEATURE_REGENERATION` (S-5, cut 4th): hides Lock/Unlock, the lock badge and SCR-030 when off. */
export const regenerationEnabled = process.env.EXPO_PUBLIC_FEATURE_REGENERATION === '1';

/** SCR-027 duration stepper (ASM-061): 15-minute steps within 15–240 min. */
export const VISIT_STEP = 15;
export const VISIT_MIN = 15;
export const VISIT_MAX = 240;
