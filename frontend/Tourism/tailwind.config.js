/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // RE-THEMED: primary/secondary used to be coral/teal (the old
        // generic starter palette). They're referenced by className
        // across every page — btn-primary, input-field's focus ring,
        // Sidebar/Navbar active states, checkbox accents, badges — so
        // repointing the token values themselves (instead of editing
        // every file that uses them) reskins the whole app to Nepal
        // colors in one place, safely, with zero JSX/logic changes.
        primary: {
          50: '#eaf0fb',
          100: '#c9d8f3',
          300: '#3f66b8',
          500: '#0B3D91', // was coral #FF5A5F — now Himalayan blue
          600: '#092f70',
          700: '#072454',
        },
        secondary: {
          500: '#1B8A5A', // was teal #00A699 — now forest green
          600: '#146c46',
        },
        dark: '#222222',

        // --- Nepal Tourism brand palette (new) ---
        himalaya: {
          50: '#eaf0fb',
          100: '#c9d8f3',
          300: '#3f66b8',
          500: '#0B3D91', // Himalayan blue
          600: '#092f70',
          700: '#072454',
        },
        forest: {
          50: '#e8f7f0',
          100: '#c3ecda',
          300: '#4bb589',
          500: '#1B8A5A', // Emerald green
          600: '#146c46',
        },
        saffron: {
          50: '#fef6e6',
          100: '#fde7bd',
          300: '#f9c665',
          500: '#F59E0B', // Warm orange / golden accent
          600: '#c97e08',
        },
        nepalred: {
          50: '#fce9ec',
          100: '#f7c0c9',
          300: '#ea5f76',
          500: '#DC143C', // Nepal flag red
          600: '#b10f30',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['"Playfair Display"', 'Georgia', 'serif'],
        devanagari: ['"Noto Sans Devanagari"', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        card: '0 6px 16px rgba(0,0,0,0.08)',
        hover: '0 10px 28px rgba(0,0,0,0.14)',
        premium: '0 10px 25px rgba(11,61,145,0.10)',
        'premium-hover': '0 20px 40px rgba(11,61,145,0.16)',
      },
      borderRadius: {
        xl2: '1.25rem',
      },
    },
  },
  plugins: [],
}