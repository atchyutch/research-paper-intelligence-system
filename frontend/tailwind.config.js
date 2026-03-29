/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          50: '#f7f7f5',
          100: '#edecea',
          200: '#d9d7d2',
          300: '#bfbbb3',
          400: '#a29c91',
          500: '#8d8578',
          600: '#7a7168',
          700: '#655d56',
          800: '#544e49',
          900: '#484440',
          950: '#272422',
        },
        paper: {
          50: '#fdfcfa',
          100: '#f9f7f3',
          200: '#f3efe8',
          300: '#e8e2d8',
          400: '#d6ccbc',
        },
        accent: {
          DEFAULT: '#c45d3e',
          light: '#d4795f',
          dark: '#a34830',
          muted: '#c45d3e1a',
        },
      },
      fontFamily: {
        display: ['"Source Serif 4"', 'Georgia', 'serif'],
        body: ['"DM Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.35s ease-out',
        'slide-right': 'slideRight 0.3s ease-out',
        'pulse-dot': 'pulseDot 1.4s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideRight: {
          '0%': { opacity: '0', transform: 'translateX(-12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseDot: {
          '0%, 80%, 100%': { opacity: '0.3', transform: 'scale(0.8)' },
          '40%': { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
}
