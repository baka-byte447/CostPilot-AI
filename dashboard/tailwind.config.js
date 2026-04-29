/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#E94F37',
        'primary-container': '#F0644D',
        'on-primary': '#F6F7EB',
        secondary: '#E94F37',
        'secondary-container': '#5A2B1F',
        'on-secondary': '#F6F7EB',
        surface: '#0f1012',
        'surface-dim': '#0f1012',
        'surface-container-lowest': '#0f1012',
        'surface-container-low': '#13151a',
        'surface-container': '#171a1f',
        'surface-container-high': '#1d2026',
        'surface-container-highest': '#22262c',
        'on-surface': '#F6F7EB',
        'on-surface-variant': 'rgba(246, 247, 235, 0.55)',
        'outline-variant': 'rgba(255, 255, 255, 0.07)',
        outline: 'rgba(255, 255, 255, 0.15)',
        background: '#0f1012',
        error: '#E94F37',
        tertiary: '#393E41',
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