import { Center, Grid, Skeleton, Stack, Text } from '@mantine/core';

export interface LoadingScreenProps {
  label?: string;
  variant?: 'default' | 'cards';
}

export function LoadingScreen({ label = 'Loading workspace', variant = 'default' }: LoadingScreenProps) {
  if (variant === 'cards') {
    return (
      <Stack gap="lg">
        <Stack gap={8}>
          <Skeleton height={12} width={80} radius="xl" />
          <Skeleton height={28} width={260} radius="md" />
          <Skeleton height={16} width={420} radius="md" />
        </Stack>
        <Grid>
          <Grid.Col span={{ base: 12, md: 6, xl: 3 }}>
            <Skeleton height={120} radius="2xl" />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 6, xl: 3 }}>
            <Skeleton height={120} radius="2xl" />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 6, xl: 3 }}>
            <Skeleton height={120} radius="2xl" />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 6, xl: 3 }}>
            <Skeleton height={120} radius="2xl" />
          </Grid.Col>
        </Grid>
        <Skeleton height={280} radius="2xl" />
      </Stack>
    );
  }

  return (
    <Center mih="60vh">
      <Stack align="center" gap="md">
        <Skeleton circle w={48} h={48} />
        <Text c="slate.6" fz="sm">{label}</Text>
      </Stack>
    </Center>
  );
}