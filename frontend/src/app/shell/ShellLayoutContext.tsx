import type { ReactNode } from 'react';
import { createContext, useContext } from 'react';


interface ShellLayoutContextValue {
  mobileOpened: boolean;
  toggleMobileNav: () => void;
  closeMobileNav: () => void;
}

const ShellLayoutContext = createContext<ShellLayoutContextValue | null>(null);

export function ShellLayoutProvider({ value, children }: { value: ShellLayoutContextValue; children: ReactNode }) {
  return <ShellLayoutContext.Provider value={value}>{children}</ShellLayoutContext.Provider>;
}

export function useShellLayout() {
  const ctx = useContext(ShellLayoutContext);
  if (!ctx) throw new Error('useShellLayout must be used inside ShellLayoutProvider');
  return ctx;
}