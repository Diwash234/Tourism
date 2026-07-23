/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Rhododendron crimson — Nepal's national flower. Primary brand color.
        primary: {
          50: '#FDF1F1',
          100: '#FBDFE0',
          300: '#E37B82',
          500: '#C0293B',
          600: '#A81F30',
          700: '#8C1826',
        },
        // Himalayan turquoise — traditional Nepali jewelry stone. Secondary accent.
        secondary: {
          50: '#EAF7F5',
          100: '#CDEEE9',
          300: '#6BBCB2',
          500: '#1E8A82',
          600: '#16746D',
          700: '#125E58',
        },
        // Marigold — used in Dashain/Tihar garlands. Warm tertiary accent.
        marigold: {
          50: '#FEF6E7',
          100: '#FCE8C3',
          300: '#F0BF6E',
          500: '#E8A33D',
          600: '#CC8A28',
          700: '#A8701E',
        },
        // Dusk-ink — replaces flat black/gray for text and dark sections.
        dark: '#1B2A4A',
        ink: {
          DEFAULT: '#1B2A4A',
          light: '#334269',
        },
        // Warm snow — replaces flat gray-50 page background.
        snow: '#FAF7F1',
        // Lungta (prayer flag) colors — the signature accent strip.
        flag: {
          blue: '#3F6FA3',
          white: '#F5F3EE',
          red: '#C0293B',
          green: '#4C9A6B',
          yellow: '#E8C547',
        },
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Manrope', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      boxShadow: {
        card: '0 6px 18px rgba(27,42,74,0.08)',
        hover: '0 12px 32px rgba(27,42,74,0.16)',
      },
      borderRadius: {
        xl2: '1.25rem',
      },
      backgroundImage: {
        'dusk-gradient': 'linear-gradient(135deg, #1B2A4A 0%, #3F6FA3 55%, #1E8A82 100%)',
        'sunrise-gradient': 'linear-gradient(135deg, #C0293B 0%, #E8A33D 100%)',
      },
    },
  },
  plugins: [],
}