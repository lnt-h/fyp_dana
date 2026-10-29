import { createContext, useContext, useState, type ReactNode } from 'react';

export const interestOptions = ['Culture', 'Beach', 'Food', 'Nature'] as const;
export const travelTypes = ['Solo', 'Couple', 'Family', 'Friends'] as const;
export type TravelType = typeof travelTypes[number];
export type Interest = typeof interestOptions[number];
type Profile = { name: string; email: string; interests: Interest[]; travelType?: TravelType };
const emptyProfile: Profile = { name: '', email: '', interests: [] };

function useAccountState() {
  const [profile, setProfile] = useState<Profile>(emptyProfile);
  const [isPreviewProfile, setIsPreviewProfile] = useState(false);
  const [reduceMotion, setReduceMotion] = useState(false);
  return {
    profile, isPreviewProfile, reduceMotion, setReduceMotion,
    updateProfile: (changes: Partial<Profile>) => setProfile(previous => ({ ...previous, ...changes })),
    startPreview: (details: Profile) => { setProfile(details); setIsPreviewProfile(true); },
    clearSession: () => { setProfile(emptyProfile); setIsPreviewProfile(false); setReduceMotion(false); },
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
