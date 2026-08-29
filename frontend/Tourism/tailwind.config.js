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
          50: '#e8f4ee',
          100: '#c7e4d5',
          200: '#9cccb6',
          300: '#67ad8e',
          400: '#3f936f',
          500: '#1f6b4d',  /* deep mountain green */
          600: '#175a40',
          700: '#114733',
          800: '#0d3526',
          900: '#08231a',
        },
        secondary: {
          50: '#fcefe8',
          100: '#f8d4c0',
          200: '#f0b08e',
          300: '#dd875c',
          400: '#cf7046',
          500: '#c2603a',  /* warm terracotta */
          600: '#a14e2d',
          700: '#7f3d25',
        },
        accent: {
          50: '#faf3e2',
          100: '#f2e0b0',
          300: '#d8ab57',
          400: '#c9993e',
          500: '#b8862f',  /* Himalayan gold */
          600: '#966b23',
        },
        dark: '#1c1917',

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
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        heading: ['Outfit', '"Playfair Display"', 'system-ui', 'sans-serif'],
        serif: ['"Playfair Display"', 'Cinzel', 'Georgia', 'serif'],
        royal: ['Cinzel', '"Playfair Display"', 'serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        devanagari: ['"Noto Sans Devanagari"', 'sans-serif'],
      },
      boxShadow: {
        card: '0 6px 16px rgba(0,0,0,0.08)',
        hover: '0 10px 28px rgba(0,0,0,0.14)',
        premium: '0 10px 25px rgba(11,61,145,0.10)',
        'premium-hover': '0 20px 40px rgba(11,61,145,0.16)',
        refero: '0 20px 40px -15px rgba(0, 0, 0, 0.07), 0 0 1px 1px rgba(0, 0, 0, 0.05)',
        'refero-dark': '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 1px 1px rgba(255, 255, 255, 0.08)',
        'glow-amber': '0 0 30px -5px rgba(245, 158, 11, 0.3)',
        'glow-purple': '0 0 35px -5px rgba(168, 85, 247, 0.3)',
        'glow-emerald': '0 0 30px -5px rgba(16, 185, 129, 0.3)',
      },
      keyframes: {
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
      },
      animation: {
        shimmer: 'shimmer 2.5s infinite',
        float: 'float 4s ease-in-out infinite',
      },
      borderRadius: {
        xl2: '1.25rem',
      },
    },
  },
  plugins: [],
}