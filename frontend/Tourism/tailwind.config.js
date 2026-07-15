/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fff5f0',
          100: '#ffe6d9',
          300: '#ff9466',
          500: '#FF5A5F',
          600: '#e6484d',
          700: '#cc3d42',
        },
        secondary: {
          500: '#00A699',
          600: '#008f84',
        },
        dark: '#222222',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 6px 16px rgba(0,0,0,0.08)',
        hover: '0 10px 28px rgba(0,0,0,0.14)',
      },
      borderRadius: {
        xl2: '1.25rem',
      },
    },
  },
  plugins: [],
}