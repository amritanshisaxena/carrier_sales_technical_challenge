/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#f4f1ea',
        card: '#fffdf8',
        ink: '#14213d',
        'ink-soft': '#56607a',
        accent: '#d97316',
        line: '#ddd6c8',
        good: '#2f7d52',
        warn: '#c2680c',
        bad: '#b3261e',
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
