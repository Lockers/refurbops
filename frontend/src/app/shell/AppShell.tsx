import { AppShell, Box, ScrollArea } from '@mantine/core';
import { Outlet } from 'react-router-dom';

import { useSession } from '@/auth/hooks/useSession';
import { AppSidebar } from '@/app/shell/AppSidebar';
import { AppTopbar } from '@/app/shell/AppTopbar';
import { ReadOnlyBanner } from '@/shared/components/ReadOnlyBanner';

export function AppShellLayout() {
  const { session } = useSession();
  const businessStatus = session?.current_business?.status ?? null;
  const isReadOnly = businessStatus === 'read_only';

  return (
    <AppShell
      header={{ height: 84 }}
      navbar={{ width: 304, breakpoint: 'sm' }}
      padding={0}
      styles={{
        main: {
          background:
            'linear-gradient(180deg, #f5f8fc 0%, #f3f6fb 46%, #eef3f9 100%)',
        },
      }}
    >
      <AppShell.Header withBorder={false} bg="transparent">
        <AppTopbar />
      </AppShell.Header>
      <AppShell.Navbar withBorder={false} bg="transparent">
        <AppSidebar />
      </AppShell.Navbar>
      <AppShell.Main>
        <ScrollArea type="never" h="calc(100vh - 84px)">
          <Box px="xl" pb="xl" pt="md">
            {isReadOnly ? <ReadOnlyBanner /> : null}
            <Outlet />
          </Box>
        </ScrollArea>
      </AppShell.Main>
    </AppShell>
  );
}

export default AppShellLayout;