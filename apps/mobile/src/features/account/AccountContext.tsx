import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useClerk, useUser } from '@clerk/expo';

export const interestOptions = ['Culture', 'Beach', 'Food', 'Nature'] as const;
export const travelTypes = ['Solo', 'Couple', 'Family', 'Friends'] as const;
export type TravelType = typeof travelTypes[number];
export type Interest = typeof interestOptions[number];
type Profile = { name: string; email: string; interests: Interest[]; travelType?: TravelType };
const emptyProfile: Profile = { name: '', email: '', interests: [] };

function useAccountState() {
  const { user, isSignedIn, isLoaded } = useUser();
  const { signOut } = useClerk();
  const [guestProfile, setGuestProfile] = useState<Profile>(emptyProfile);
  const [reduceMotion, setReduceMotion] = useState(false);
  useEffect(() => {
    setGuestProfile(emptyProfile);
    setReduceMotion(false);
  }, [user?.id]);
  const stored = user?.unsafeMetadata;
  const interests = Array.isArray(stored?.interests) ? stored.interests.filter((value): value is Interest => interestOptions.includes(value as Interest)) : [];
  const travelType = travelTypes.includes(stored?.travelType as TravelType) ? stored?.travelType as TravelType : undefined;
  const profile: Profile = user ? { name: user.fullName ?? '', email: user.primaryEmailAddress?.emailAddress ?? '', interests, travelType } : guestProfile;
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
