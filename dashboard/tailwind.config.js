/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg:           "#080C14",
        surface:      "#0D1421",
        surfaceHigh:  "#111B2E",
        surfaceBorder:"#1A2540",
        text:         "#E2EAF8",
        textMuted:    "#5A7090",
        textDim:      "#2E4060",
        cyan:         "#00D4FF",
        cyanDim:      "rgba(0,212,255,0.12)",
        green:        "#00E599",
        greenDim:     "rgba(0,229,153,0.12)",
        amber:        "#FFB020",
        amberDim:     "rgba(255,176,32,0.12)",
        red:          "#FF4D6A",
        redDim:       "rgba(255,77,106,0.12)",
        purple:       "#A78BFA",
        purpleDim:    "rgba(167,139,250,0.12)",
      },
      fontFamily: {
        sans:  ['DM Sans', 'system-ui', 'sans-serif'],
        mono:  ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        card:    '0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px rgba(26,37,64,0.8)',
        glow:    '0 0 20px rgba(0,212,255,0.15)',
        glowSm:  '0 0 10px rgba(0,212,255,0.1)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'fade-in':    'fadeIn 0.4s ease both',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [],
}