/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  // Light-only. Warm paper #F8F6F1. Electric blue #2563EB. No dark toggle.
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
        '4xl': ['2.5rem',   { lineHeight: '1.1' }],
        '5xl': ['3.5rem',   { lineHeight: '1.05' }],
        '6xl': ['4.5rem',   { lineHeight: '1.02' }],
        '7xl': ['5.5rem',   { lineHeight: '1.0' }],
      },
      colors: {
        // Paper base
        paper: '#F8F6F1',
        // Electric blue accent
        accent: {
          DEFAULT: '#1D4ED8',
          hover: '#1E40AF',
          light: '#EFF6FF',
          text: '#1D4ED8',
        },
        // Status badge colors
        status: {
          live: { bg: '#DCFCE7', text: '#15803D' },
          sunset: { bg: '#FEF9C3', text: '#854D0E' },
          sold: { bg: '#EFF6FF', text: '#1D4ED8' },
        },
      },
      maxWidth: {
        '7xl': '72rem',
        content: '46rem',
      },
      letterSpacing: {
        tightest: '-0.04em',
        tight2: '-0.025em',
      },
    },
  },
};
