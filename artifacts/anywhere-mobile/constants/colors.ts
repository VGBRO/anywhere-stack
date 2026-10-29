/**
 * Semantic design tokens for the mobile app.
 *
 * These tokens mirror the naming conventions used in web artifacts (index.css)
 * so that multi-artifact projects share a cohesive visual identity.
 *
 * Replace the placeholder values below with values that match the project's
 * brand. If a sibling web artifact exists, read its index.css and convert the
 * HSL values to hex so both artifacts use the same palette.
 *
 * To add dark mode, add a `dark` key with the same token names.
 * The useColors() hook will automatically pick it up.
 */

const colors = {
  light: {
    text: '#1d1d1f',
    tint: '#0066cc',
    background: '#f5f5f7',
    foreground: '#1d1d1f',
    card: '#ffffff',
    cardForeground: '#1d1d1f',
    primary: '#0066cc',
    primaryForeground: '#ffffff',
    secondary: '#f0f0f0',
    secondaryForeground: '#1d1d1f',
    muted: '#f0f0f0',
    mutedForeground: '#7a7a7a',
    accent: '#e5f1fc',
    accentForeground: '#0066cc',
    destructive: '#c73737',
    destructiveForeground: '#ffffff',
    border: 'rgba(29,29,31,0.1)',
    input: 'rgba(29,29,31,0.14)',
    glassSurface: 'rgba(255,255,255,0.72)',
    glassStrong: 'rgba(255,255,255,0.82)',
    glassBorder: 'rgba(255,255,255,0.9)',
    skyTop: '#1a3d82',
    skyMid: '#4a80c2',
    skyBottom: '#c5ddf0',
    horizon: '#2a4878',
    horizonFar: '#9bb3d5',
    water: '#1e3870',
    treeLine: '#1a2345',
    firmBackground: '#ececec',
    firmGold: '#b48c50',
    offline: '#ff3b30',
    success: '#34a853',
    warning: '#ff9500',
  },
  dark: {
    text: '#f3f7fb',
    tint: '#65b5ff',
    background: '#091827',
    foreground: '#f3f7fb',
    card: 'rgba(19,39,59,0.76)',
    cardForeground: '#f3f7fb',
    primary: '#2997ff',
    primaryForeground: '#061728',
    secondary: 'rgba(255,255,255,0.08)',
    secondaryForeground: '#e5eef8',
    muted: 'rgba(255,255,255,0.08)',
    mutedForeground: '#afbdca',
    accent: 'rgba(41,151,255,0.16)',
    accentForeground: '#9bd0ff',
    destructive: '#ff7777',
    destructiveForeground: '#2b1111',
    border: 'rgba(255,255,255,0.12)',
    input: 'rgba(255,255,255,0.16)',
    glassSurface: 'rgba(17,37,57,0.67)',
    glassStrong: 'rgba(12,29,46,0.88)',
    glassBorder: 'rgba(255,255,255,0.17)',
    skyTop: '#09263f',
    skyMid: '#123a59',
    skyBottom: '#091827',
    horizon: '#315a76',
    horizonFar: '#497390',
    water: '#12304e',
    treeLine: '#071321',
    firmBackground: '#091827',
    firmGold: '#d8b879',
    offline: '#ff7777',
    success: '#75d6ad',
    warning: '#f2bb72',
  },
  radius: 18,
};

export default colors;
