import type { PropsWithChildren, ReactNode } from 'react';
import {
  Box,
  Grid,
  Group,
  List,
  Paper,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from '@mantine/core';
import { IconCheck, IconCookie, IconLock } from '@tabler/icons-react';

import { BrandMark } from '@/shared/components/BrandMark';

const highlights = [
  'Organisation, business, and site scope stays explicit.',
  'Read only and suspended states stay visible, not hidden.',
  'Session control is server-side and cookie-based.',
];

interface AuthSplitLayoutProps extends PropsWithChildren {
  eyebrow: string;
  title: string;
  description: string;
  badge?: ReactNode;
  footer?: ReactNode;
}

export function AuthSplitLayout({
  eyebrow,
  title,
  description,
  badge,
  footer,
  children,
}: AuthSplitLayoutProps) {
  return (
    <Box
      mih="100vh"
      px="lg"
      py="xl"
      style={{
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <Paper
        radius="3xl"
        withBorder
        maw={1280}
        mx="auto"
        w="100%"
        style={{
          overflow: 'hidden',
          borderColor: 'rgba(87, 105, 129, 0.16)',
          background: 'rgba(255,255,255,0.94)',
          boxShadow: '0 30px 80px rgba(15, 23, 42, 0.10)',
        }}
      >
        <Grid>
          <Grid.Col span={{ base: 12, md: 7 }}>
            <Box
              p={{ base: 'xl', md: '3rem' }}
              h="100%"
              style={{
                background: 'linear-gradient(155deg, rgba(13,49,120,1) 0%, rgba(23,25,30,1) 44%, rgba(15,23,42,1) 100%)',
                color: 'white',
              }}
            >
              <Stack justify="space-between" h="100%" gap="2.5rem">
                <Stack gap="xl">
                  <BrandMark inverted />

                  <Stack gap="md" maw={560}>
                    <Text
                      fz="xs"
                      fw={700}
                      tt="uppercase"
                      c="rgba(255,255,255,0.68)"
                      style={{ letterSpacing: '0.08em' }}
                    >
                      {eyebrow}
                    </Text>
                    <Title order={1} c="white" maw={560}>
                      {title}
                    </Title>
                    <Text c="rgba(255,255,255,0.78)" fz="lg" maw={560}>
                      {description}
                    </Text>
                  </Stack>

                  <List
                    spacing="md"
                    icon={
                      <ThemeIcon color="brand" radius="xl" size={22} variant="filled">
                        <IconCheck size={14} />
                      </ThemeIcon>
                    }
                  >
                    {highlights.map((item) => (
                      <List.Item key={item}>
                        <Text c="rgba(255,255,255,0.82)">{item}</Text>
                      </List.Item>
                    ))}
                  </List>
                </Stack>

                <Group gap="md" wrap="wrap">
                  <Paper radius="2xl" p="md" bg="rgba(255,255,255,0.06)" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
                    <Group wrap="nowrap" align="flex-start">
                      <ThemeIcon radius="xl" color="brand" variant="light">
                        <IconLock size={16} />
                      </ThemeIcon>
                      <div>
                        <Text c="white" fw={700} fz="sm">Secure web session</Text>
                        <Text c="rgba(255,255,255,0.68)" fz="sm">Browser tokens are not stored in local storage.</Text>
                      </div>
                    </Group>
                  </Paper>

                  <Paper radius="2xl" p="md" bg="rgba(255,255,255,0.06)" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
                    <Group wrap="nowrap" align="flex-start">
                      <ThemeIcon radius="xl" color="brand" variant="light">
                        <IconCookie size={16} />
                      </ThemeIcon>
                      <div>
                        <Text c="white" fw={700} fz="sm">Backend-led auth</Text>
                        <Text c="rgba(255,255,255,0.68)" fz="sm">Frontend follows the platform state exposed by the API.</Text>
                      </div>
                    </Group>
                  </Paper>
                </Group>
              </Stack>
            </Box>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 5 }}>
            <Box p={{ base: 'xl', md: '3rem' }} h="100%" style={{ display: 'flex', alignItems: 'center' }}>
              <Stack gap="xl" w="100%" maw={440} mx="auto">
                <Stack gap={8}>
                  {badge}
                </Stack>

                {children}

                {footer ?? (
                  <Group justify="space-between">
                    <Text size="sm" c="slate.6" component="a" href="#" style={{ cursor: 'pointer' }}>Need an invite?</Text>
                    <Text size="sm" c="slate.6" component="a" href="#" style={{ cursor: 'pointer' }}>Forgot password?</Text>
                  </Group>
                )}
              </Stack>
            </Box>
          </Grid.Col>
        </Grid>
      </Paper>
    </Box>
  );
}