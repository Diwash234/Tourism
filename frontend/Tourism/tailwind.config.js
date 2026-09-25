/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  // Dark theme is class-driven: ThemeContext toggles `.dark` on <html> and
  // persists the choice in localStorage (key: ny_theme).
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Semantic tokens from the UI audit â€” single source of truth for
        // role-based colors. Existing per-page classes keep working; new
        // code should use these.
        brand: {
          DEFAULT: '#075B48', // Nepal green â€” primary actions and active nav
          hover: '#063B32',   // dark Nepal green â€” hover/pressed
          light: '#EFF8F4',   // soft green surfaces
          mint: '#63E6BE',
          gold: '#F5B51B',
          gradientFrom: '#063B32',
          gradientTo: '#087F63',
         },
         // Compatibility alias for older utilities and token regression checks.
         legacyBrand: { hover: '#065f46' },
         // NOTE: a bare `accent: '#f59e0b'` string used to live here and was
        // silently shadowed by the accent{} scale object below (duplicate key
        // in the same literal â€” last one wins). Removed; use accent-500 or
        // saffron-500 for the amber attention color.
        surface: {
          light: '#f9fafb', // gray-50 â€” page background (light theme)
          dark: '#0f172a',  // slate-900 â€” page background (dark theme)
        },
        // ONE Nepal-Yatra nav palette â€” shared tokens for Navbar, Sidebar and
        // nav-adjacent chrome. Hex values match the emerald shades these
        // components already used; consolidating here means future re-theming
        // happens in one place instead of ~30 scattered utility classes.
        nav: {
          base: '#042A24',
          surface: '#063B32',
          active: '#075B48',
          hover: '#063B32',
          strong: '#087F63',
          tint: '#EFF8F4',
          tintStrong: '#DDEFE7',
          deep: '#063B32',
          darkText: '#63E6BE',
          dark: '#0B1714',
          darkAlt: '#13231F',
        },
        danger: '#C62828',
        ai: '#087F63',
        // RE-THEMED: primary/secondary used to be coral/teal (the old
        // generic starter palette). They're referenced by className
        // across every page â€” btn-primary, input-field's focus ring,
        // Sidebar/Navbar active states, checkbox accents, badges â€” so
        // repointing the token values themselves (instead of editing
        // every file that uses them) reskins the whole app to Nepal
        // colors in one place, safely, with zero JSX/logic changes.
        primary: {
          50: '#EFF8F4',
          100: '#DDEFE7',
          200: '#BDEBD9',
          300: '#87D5BA',
          400: '#43B58F',
          500: '#087F63',
          600: '#075B48',
          700: '#063B32',
          800: '#042A24',
          900: '#042A24',
        },
        secondary: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#2563A6',
          600: '#1D4F87',
          700: '#163B64',
        },
        accent: {
          50: '#FFF7DE',
          100: '#FDE9AF',
          300: '#F5C84B',
          400: '#F5B51B',
          500: '#E9A915',
          600: '#B77D0B',
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
        // CEE "AI Index" reference palette â€” deep indigo anchor + glacier/turquoise data accents.
        cee: {
          bg: '#F9FAFE',
          glacier: '#8BB2FC',
          blue: '#71A0F7',
          indigo: '#3E58B0',
          navy: '#231E54',
          ink: '#0d1330',
          night: '#070c20',
          lavender: '#8E70AE',
          turquoise: '#70B1AB',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '"Segoe UI"', 'Roboto', 'sans-serif'],
        heading: ['Inter', 'system-ui', '"Segoe UI"', 'Roboto', 'sans-serif'],
        serif: ['"Playfair Display"', 'Cinzel', 'Georgia', 'serif'],
        royal: ['Cinzel', '"Playfair Display"', 'serif'],
        // CEE "AI Index" reference typeface â€” clean, geometric, data-confident.
        ubuntu: ['Ubuntu', 'Inter', 'system-ui', 'sans-serif'],
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