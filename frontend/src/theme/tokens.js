const palette = {
  background: '#0C0E12',
  card: '#12151C',
  border: '#1A1D25',
  textPrimary: '#E8ECF0',
  textSecondary: '#A5AAB2',
  cobalt: '#3A8BFF',
  cyan: '#36C6F0',
  primary: '#3A8BFF',
  primaryDark: '#1F5EB5',
  success: '#4CAF50',
  warning: '#D0A036',
  danger: '#D84545',
  info: '#3A8BFF',
  gray100: '#f5f7fb',
  gray200: '#e1e6f2',
  gray300: '#aaaebc',
  gray400: '#7b8093',
  gray500: '#4d5465',
  gray600: '#2b2f3b',
}

const typography = {
  fontPrimary: "'Inter', 'IBM Plex Sans', system-ui, sans-serif",
  fontSecondary: "'IBM Plex Sans', 'Inter', system-ui, sans-serif",
  fontMono: "'JetBrains Mono', 'SFMono-Regular', Menlo, monospace",
  weights: {
    thin: 300,
    normal: 400,
    medium: 500,
    bold: 600,
  },
  headings: {
    h1: '24px',
    h2: '20px',
    h3: '16px',
  },
  tracking: {
    tight: '-0.01em',
    normal: '0.02em',
    loose: '0.18em',
  },
}

const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
  xxxl: '64px',
  gutter: '16px',
}
spacing.spaceXS = spacing.xs
spacing.spaceSM = spacing.sm
spacing.spaceMD = spacing.md
spacing.spaceLG = spacing.lg
spacing.spaceXL = spacing.xl
spacing.spaceXXL = spacing.xxl
spacing.spaceXXXL = spacing.xxxl

const radii = {
  xsmall: '4px',
  small: '6px',
  base: '10px',
  medium: '12px',
  large: '18px',
  card: '14px',
  pill: '999px',
}

const shadows = {
  shadow1: '0 4px 10px rgba(6, 8, 20, 0.5)',
  shadow2: '0 12px 25px rgba(6, 8, 20, 0.65)',
  shadow3: '0 20px 40px rgba(4, 6, 18, 0.75)',
  focus: '0 0 0 2px rgba(58, 139, 255, 0.4)',
}

const transitions = {
  fast: '0.15s ease-out',
  base: '0.3s ease',
  slow: '0.45s ease',
  focus: '0.25s ease-out',
  transform: '0.35s cubic-bezier(0.25, 0.8, 0.25, 1)',
}

const layout = {
  maxWidth: '1200px',
  gutter: 'var(--ketter-spacing-lg)',
  gridColumns: 12,
  gridGap: 'var(--ketter-grid-gap)',
  containerWidth: 'var(--ketter-ui-container-width)',
}

const card = {
  borderRadius: 'var(--ketter-card-radius)',
  shadow: 'var(--ketter-card-shadow)',
}

export { palette, typography, spacing, radii, shadows }
export { transitions, layout, card }
export default { palette, typography, spacing, radii, shadows, transitions, layout, card }
