/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      backgroundColor: {
        'primary': '#0a0a0b',
        'secondary': '#111113',
        'elevated': '#18181b',
        'border': '#27272a',
      },
      textColor: {
        'primary': '#fafafa',
        'secondary': '#a1a1aa',
        'muted': '#52525b',
      },
      borderColor: {
        'primary': '#0a0a0b',
        'secondary': '#111113',
        'elevated': '#18181b',
        'border': '#27272a',
      },
      colors: {
        'primary': '#fafafa',
        'secondary': '#a1a1aa',
        'muted': '#52525b',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Monaco', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '10px',
      },
      width: {
        sidebar: '320px',
        overlay: '580px',
      },
    },
  },
  plugins: [],
};
