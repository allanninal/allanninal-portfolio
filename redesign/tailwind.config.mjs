/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  darkMode: 'class',
  // Dark-only "telemetry console": near-black ground, cyan signal, indigo second.
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans Variable"', '"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['"Plus Jakarta Sans Variable"', '"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'monospace'],
      },
      fontSize: {
        'xs':  ['0.75rem',  { lineHeight: '1.6' }],
        'sm':  ['0.875rem', { lineHeight: '1.65' }],
        'base':['1rem',     { lineHeight: '1.7' }],
        'lg':  ['1.125rem', { lineHeight: '1.65' }],
        'xl':  ['1.25rem',  { lineHeight: '1.5' }],
        '2xl': ['1.5rem',   { lineHeight: '1.3' }],
        '3xl': ['1.875rem', { lineHeight: '1.2' }],
        '4xl': ['2.5rem',   { lineHeight: '1.08' }],
        '5xl': ['3.25rem',  { lineHeight: '1.03' }],
        '6xl': ['4rem',     { lineHeight: '1.0' }],
        '7xl': ['5rem',     { lineHeight: '0.98' }],
      },
      colors: {
        // Ground
        ink: {
          950: '#05070E',
          900: '#080C17',
          850: '#0B1120',
          800: '#111A2E',
          700: '#1B2740',
        },
        // Cyan signal
        accent: {
          DEFAULT: '#22D3EE',
          bright: '#67E8F9',
          deep: '#0E7490',
          hover: '#67E8F9',
          light: 'rgba(34,211,238,0.10)',
          text: '#22D3EE',
        },
        indigo2: '#818CF8',
      },
      maxWidth: {
        '7xl': '76rem',
        content: '46rem',
      },
      letterSpacing: {
        tightest: '-0.045em',
        tight2: '-0.03em',
      },
    },
  },
};
