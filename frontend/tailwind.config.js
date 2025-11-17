/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#165DFF',
        secondary: '#6B7280',
        dark: '#1E293B',
        light: '#F8FAFC',
        'dark-bg': '#0F172A',
        'dark-card': '#1E293B',
        'dark-input': '#1E293B',
        'dark-hover': '#334155',
        'light-hover': '#F1F5F9'
      },
      fontFamily: {
        inter: ['Inter', 'system-ui', 'sans-serif']
      }
    },
  },
  plugins: [],
}

