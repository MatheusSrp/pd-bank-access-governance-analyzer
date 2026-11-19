/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
      colors: {
        ink: { 950: '#080f1e', 900: '#0d1729', 800: '#142238', 700: '#1c2d46' },
        muted: '#91a3be',
        brand: '#557cff',
        cyan: '#22c7c9',
        violet: '#8b6cff',
        success: '#20c997',
        warning: '#f5b942',
        critical: '#f06470',
      },
      boxShadow: { card: '0 12px 36px rgba(2, 8, 23, 0.18)' },
      borderRadius: { '2xl': '1.125rem' },
    },
  },
  plugins: [],
}
