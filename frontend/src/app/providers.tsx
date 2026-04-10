import { ColorSchemeScript, MantineProvider, localStorageColorSchemeManager } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClientProvider } from '@tanstack/react-query';
import type { PropsWithChildren } from 'react';

import { theme } from '@/app/theme/theme';
import { queryClient } from '@/shared/lib/query-client';

const colorSchemeManager = localStorageColorSchemeManager();

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <>
      <ColorSchemeScript defaultColorScheme="light" localStorageKey="refurbops-color-scheme" />
      <MantineProvider
        theme={theme}
        defaultColorScheme="light"
        colorSchemeManager={colorSchemeManager}
      >
        <QueryClientProvider client={queryClient}>
          <Notifications position="top-right" zIndex={2000} />
          {children}
        </QueryClientProvider>
      </MantineProvider>
    </>
  );
}