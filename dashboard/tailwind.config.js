/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#57f1db',
        'primary-container': '#2dd4bf',
        'on-primary': '#003731',
        secondary: '#d0bcff',
        'secondary-container': '#571bc1',
        'on-secondary': '#3c0091',
        surface: '#10131a',
        'surface-dim': '#10131a',
        'surface-container-lowest': '#0b0e14',
        'surface-container-low': '#191c22',
        'surface-container': '#1d2026',
        'surface-container-high': '#272a31',
        'surface-container-highest': '#32353c',
        'on-surface': '#e1e2eb',
        'on-surface-variant': '#bacac5',
        'outline-variant': '#3c4a46',
        outline: '#859490',
        background: '#10131a',
        error: '#ffb4ab',
        tertiary: '#d1d9f3',
      },
      fontFamily: {
        headline: ['Manrope'],
        body: ['Inter'],
        label: ['Inter'],
      },
      borderRadius: {
        DEFAULT: '1rem',
        lg: '2rem',
        xl: '3rem',
        full: '9999px',
      },
    },
  },
  plugins: [],
}