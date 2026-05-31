/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        padel: {
          50: '#eff6ff',
          600: '#1e40af',
          700: '#1d3a9e',
        },
      },
    },
  },
  plugins: [],
}
