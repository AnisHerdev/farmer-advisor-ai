/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        soil: {
          950: '#111a14',
          900: '#14211a',
          800: '#1b2d23',
          700: '#284234',
          600: '#3d5a49',
          500: '#527360',
          400: '#759783',
          300: '#a3beaf',
          200: '#cfe0d6',
          100: '#eaf2ed',
          50: '#f6faf7',
        },
        forest: {
          900: '#0e2b1f',
          800: '#143c2c',
          700: '#1b4332',
          600: '#235942',
          500: '#2d6a4f',
          400: '#40916c',
          300: '#52b788',
          200: '#74c69d',
          100: '#b7e4c7',
          50: '#d8f3dc',
        },
        loam: {
          600: '#8c583f',
          500: '#b07d62',
          400: '#cb997e',
          300: '#ddbea9',
          200: '#eddcd2',
          100: '#f6eee7',
          50: '#fbf7f4',
        },
        harvest: {
          600: '#b38234',
          500: '#d4a373',
          400: '#e0b589',
          300: '#eecfa7',
          200: '#faedcd',
          100: '#fefae0',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
