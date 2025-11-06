/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e0f7f5',
          100: '#b2ede8',
          200: '#80e3db',
          300: '#4dd9ce',
          400: '#1FA08F',
          500: '#1a8a7a',
          600: '#157465',
          700: '#115e51',
          800: '#0d4a3f',
          900: '#09362d',
        },
        secondary: {
          50: '#f0f4f6',
          100: '#d9e4e8',
          200: '#c2d4da',
          300: '#9bb8c2',
          400: '#749caa',
          500: '#486876',
          600: '#3a5360',
          700: '#2c3e4a',
          800: '#1e2934',
          900: '#10141e',
        },
        neutral: {
          50: '#fafafa',
          100: '#f5f5f5',
          200: '#eeeeee',
          300: '#e0e0e0',
          400: '#BDB7C0',
          500: '#9e9e9e',
          600: '#757575',
          700: '#616161',
          800: '#424242',
          900: '#131E32',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

