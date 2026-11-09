import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { useClerk, useUser } from '@clerk/expo';
import { useTranslation } from 'react-i18next';

import { fetchPreferences, savePreferences, toPreferencesWrite } from '../../lib/api/sourceAccount';
import { demoNoAuth } from '../../lib/demoAuth';

export const interestOptions = ['Culture', 'Beach', 'Food', 'Nature'] as const;
export const travelTypes = ['Solo', 'Couple', 'Family', 'Friends'] as const;
export type TravelType = typeof travelTypes[number];
export type Interest = typeof interestOptions[number];
type Profile = { name: string; email: string; interests: Interest[]; travelType?: TravelType };
const emptyProfile: Profile = { name: '', email: '', interests: [] };

/** Profile interest → contract category code stored in `interest_category_codes` (API-004/005). */
export const interestCategoryCode: Record<Interest, string> = { Beach: 'BEACH', Culture: 'HERITAGE', Food: 'FOOD', Nature: 'NATURE' };
const mappedCodes = new Set(Object.values(interestCategoryCode));

/** Server codes → profile interests (codes outside the four profile interests are kept server-side only). */
const interestsFromCodes = (codes: string[]): Interest[] => {
  const upper = new Set(codes.map(code => code.toUpperCase()));
  return interestOptions.filter(interest => upper.has(interestCategoryCode[interest]));
};

/**
 * Writes the interests to API-005 as a full replace built on the current server preferences, so pace, modes, day window
 * and any other interest codes the planner saved are kept.
 */
async function pushInterests(interests: Interest[]): Promise<void> {
  const current = await fetchPreferences();
  const others = current.interest_category_codes.filter(code => !mappedCodes.has(code.toUpperCase()));
  const codes = [...others, ...interests.map(interest => interestCategoryCode[interest])].slice(0, 20);
  await savePreferences(toPreferencesWrite(current, { interest_category_codes: codes }));
}

function useAccountState() {
  const { t } = useTranslation();
  const { user, isSignedIn, isLoaded } = useUser();
  const { signOut } = useClerk();
  const [guestProfile, setGuestProfile] = useState<Profile>(emptyProfile);
  /** Interests from API-004, loaded once per account; null until loaded (or when the call failed). */
  const [serverInterests, setServerInterests] = useState<Interest[] | null>(null);
  const [reduceMotion, setReduceMotion] = useState(false);
  const accountKey = demoNoAuth ? 'demo' : isSignedIn ? user?.id ?? null : null;
  useEffect(() => {
    setGuestProfile(emptyProfile);
    setReduceMotion(false);
    setServerInterests(null);
    if (!accountKey) return;
    let alive = true;
    fetchPreferences()
      .then(prefs => { if (alive) setServerInterests(interestsFromCodes(prefs.interest_category_codes)); })
      .catch(() => undefined); // offline or signed out: Clerk metadata (or local state) stays the source
    return () => { alive = false; };
  }, [accountKey]);

  const stored = user?.unsafeMetadata;
  const clerkInterests = Array.isArray(stored?.interests) ? stored.interests.filter((value): value is Interest => interestOptions.includes(value as Interest)) : null;
  const interests = clerkInterests && clerkInterests.length ? clerkInterests : serverInterests ?? clerkInterests ?? [];
  const travelType = travelTypes.includes(stored?.travelType as TravelType) ? stored?.travelType as TravelType : undefined;
  const profile: Profile = user ? { name: user.fullName ?? '', email: user.primaryEmailAddress?.emailAddress ?? '', interests, travelType } : guestProfile;
  const syncInterests = useCallback(async (next: Interest[] | undefined) => {
    if (!next) return;
    await pushInterests(next);
    setServerInterests(next);
  }, []);

  if (demoNoAuth) {
    // Shared demo user: always signed in, name and travel type kept in local state only (never the Clerk session);
    // interests also go to API-005 so the planner and other devices see them.
    const demoProfile: Profile = {
      ...guestProfile,
      interests: guestProfile.interests.length ? guestProfile.interests : serverInterests ?? [],
      name: guestProfile.name || t('account.profile.guestName'),
    };
    return {
      profile: demoProfile, isSignedIn: true, isLoaded: true, reduceMotion, setReduceMotion,
      updateProfile: async (changes: Partial<Omit<Profile, 'email'>>) => {
        await syncInterests(changes.interests);
        setGuestProfile(previous => ({ ...previous, ...changes }));
      },
      clearSession: async () => { setGuestProfile(emptyProfile); setReduceMotion(false); },
    };
  }
  return {
    profile, isSignedIn: Boolean(isSignedIn), isLoaded, reduceMotion, setReduceMotion,
    updateProfile: async (changes: Partial<Omit<Profile, 'email'>>) => {
      if (!user) { setGuestProfile(previous => ({ ...previous, ...changes })); return; }
      const [firstName, ...lastName] = (changes.name ?? profile.name).trim().split(/\s+/);
      await user.update({
        ...(changes.name !== undefined ? { firstName, lastName: lastName.join(' ') } : {}),
        unsafeMetadata: {
          ...user.unsafeMetadata,
          interests: changes.interests ?? profile.interests,
          travelType: changes.travelType ?? profile.travelType ?? null,
        },
      });
      await syncInterests(changes.interests);
    },
    clearSession: async () => {
      if (user) await signOut();
      setGuestProfile(emptyProfile); setReduceMotion(false);
    },
  };
}

const AccountContext = createContext<ReturnType<typeof useAccountState> | null>(null);
export function AccountProvider({ children }: { children: ReactNode }) {
  const value = useAccountState();
  return <AccountContext.Provider value={value}>{children}</AccountContext.Provider>;
}
export function useAccount() {
  const account = useContext(AccountContext);
  if (!account) throw new Error('AccountProvider is required');
  return account;
}
