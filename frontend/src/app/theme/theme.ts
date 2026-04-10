import { createTheme } from '@mantine/core';

const brand = [
  '#eef5ff',
  '#ddeaff',
  '#bfd6ff',
  '#93b7ff',
  '#6798ff',
  '#3f7dfa',
  '#1d63ed',
  '#144ec3',
  '#103f9a',
  '#0d3178',
] as const;

const slate = [
  '#f5f7fb',
  '#e8edf5',
  '#d2dbe7',
  '#b3c1d4',
  '#8fa0b8',
  '#6f819d',
  '#576981',
  '#44546a',
  '#2f3b4e',
  '#182131',
] as const;

const ink = [
  '#e8ebf1',
  '#cfd6e1',
  '#aab7c7',
  '#8496ad',
  '#667990',
  '#506075',
  '#3a4657',
  '#283140',
  '#171d27',
  '#0b0f16',
] as const;

export const theme = createTheme({
  primaryColor: 'brand',
  colors: {
    brand,
    slate,
    ink,
  },
  white: '#ffffff',
  black: '#17191E',
  primaryShade: 6,
  defaultRadius: 'md',
  fontFamily:
    '"Inter", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  headings: {
    fontFamily:
      '"Inter", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontWeight: '800',
    sizes: {
      h1: { fontSize: '2.25rem', lineHeight: '1.1', fontWeight: '800' },
      h2: { fontSize: '1.625rem', lineHeight: '1.15', fontWeight: '800' },
      h3: { fontSize: '1.125rem', lineHeight: '1.2', fontWeight: '700' },
    },
  },
  radius: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '32px',
  },
  shadows: {
    xs: '0 1px 2px rgba(15, 23, 42, 0.04)',
    sm: '0 2px 8px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04)',
    md: '0 8px 24px rgba(15, 23, 42, 0.08), 0 2px 6px rgba(15, 23, 42, 0.04)',
    lg: '0 16px 40px rgba(15, 23, 42, 0.10), 0 4px 12px rgba(15, 23, 42, 0.04)',
    xl: '0 24px 64px rgba(15, 23, 42, 0.14), 0 8px 20px rgba(15, 23, 42, 0.06)',
  },
  other: {
    panelBorder: 'rgba(87, 105, 129, 0.14)',
    panelBorderLight: 'rgba(87, 105, 129, 0.10)',
    panelBorderDark: 'rgba(255, 255, 255, 0.08)',
    glassBg: 'rgba(255, 255, 255, 0.88)',
    glassBgDark: 'rgba(20, 22, 28, 0.92)',
    glassPanel: 'rgba(255, 255, 255, 0.06)',
    glassPanelBorder: 'rgba(255, 255, 255, 0.08)',
    surfaceGradient: 'linear-gradient(180deg, rgba(255,255,255,0.97) 0%, #ffffff 100%)',
    surfaceGradientDark: 'linear-gradient(180deg, rgba(30,33,40,0.97) 0%, #1a1c22 100%)',
    sidebarGradient: 'linear-gradient(180deg, #132a63 0%, #0f214d 48%, #0b1737 100%)',
    authPanelGradient: 'linear-gradient(155deg, rgba(13,49,120,1) 0%, rgba(23,25,30,1) 44%, rgba(15,23,42,1) 100%)',
    mainBackground: 'linear-gradient(180deg, #f5f8fc 0%, #f3f6fb 46%, #eef3f9 100%)',
    mainBackgroundDark: 'linear-gradient(180deg, #1a1d24 0%, #15171c 100%)',
  },
  components: {
    AppShell: {
      defaultProps: {
        padding: 'lg',
      },
    },
    Button: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        root: {
          transition: 'all 150ms ease',
        },
      },
    },
    Paper: {
      defaultProps: {
        radius: '2xl',
      },
    },
    Card: {
      defaultProps: {
        radius: '2xl',
        shadow: 'xs',
        withBorder: true,
      },
      styles: {
        root: {
          transition: 'box-shadow 200ms ease, transform 200ms ease',
        },
      },
    },
    TextInput: {
      defaultProps: {
        radius: 'md',
        size: 'md',
      },
    },
    PasswordInput: {
      defaultProps: {
        radius: 'md',
        size: 'md',
      },
    },
    Select: {
      defaultProps: {
        radius: 'md',
        size: 'md',
      },
    },
    Badge: {
      defaultProps: {
        radius: 'sm',
      },
    },
    NavLink: {
      styles: {
        root: {
          borderRadius: '12px',
          transition: 'all 150ms ease',
        },
      },
    },
    ActionIcon: {
      styles: {
        root: {
          transition: 'all 150ms ease',
        },
      },
    },
  },
});