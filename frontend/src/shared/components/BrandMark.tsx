import { Box, Group, Text } from '@mantine/core';

export interface BrandMarkProps {
  compact?: boolean;
  inverted?: boolean;
}

export function BrandMark({ compact = false, inverted = false }: BrandMarkProps) {
  const textColor = inverted ? 'white' : 'ink.8';
  const subColor = inverted ? 'rgba(255,255,255,0.72)' : 'slate.6';

  return (
    <Group gap="sm" wrap="nowrap">
      <Box
        aria-hidden="true"
        style={{
          width: compact ? 36 : 44,
          height: compact ? 36 : 44,
          borderRadius: compact ? 12 : 14,
          position: 'relative',
          overflow: 'hidden',
          background: 'linear-gradient(135deg, #1D63ED 0%, #5B9CFF 100%)',
          boxShadow: '0 10px 24px rgba(29, 99, 237, 0.25)',
        }}
      >
        <Box
          style={{
            position: 'absolute',
            inset: 8,
            borderRadius: compact ? 8 : 10,
            border: '1px solid rgba(255,255,255,0.30)',
          }}
        />
        <Box
          style={{
            position: 'absolute',
            right: 8,
            bottom: 8,
            width: compact ? 12 : 14,
            height: compact ? 12 : 14,
            borderRadius: 999,
            background: 'rgba(255,255,255,0.94)',
          }}
        />
      </Box>
      {compact ? null : (
        <div>
          <Text c={textColor} fw={800} fz="lg" lh={1.1}>
            RefurbOps
          </Text>
          <Text c={subColor} fz="xs" fw={500}>
            Device operations platform
          </Text>
        </div>
      )}
    </Group>
  );
}
