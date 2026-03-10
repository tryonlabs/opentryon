/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    'node_modules/flowbite-react/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        Lato: ["var(--font-lato)", "Lato", "sans-serif"],
        Roboto: ["var(--font-roboto)", "Roboto", "sans-serif"],
        OpenSans: ["var(--font-open-sans)", "Open Sans", "sans-serif"],
        Mulish : ["var(--font-mulish)", 'Mulish', 'sans-serif'],
        baloo : ["var(--font-baloo)", 'Baloo 2', 'sans-serif'],
        proxima: ['Proxima Nova', 'sans-serif'],
        Readex_pro : ["var(--font-readex-pro)", "Readex Pro", 'sans-serif'],
      },
      colors :{
        'bgr' : "#4D6F9799",  
        'selected' : '#BE3144',
        'lite-red' : '#EFCBCB',
        'pale-red' : '#FCEFEF66',
        'opac-auth' : 'rgba(255, 255, 255, 0.30)',
        'opac-input' : 'rgba(255, 255, 255, 0.10)',
        'opac-gallery': 'rgba(255, 255, 255, 0.50)',
        'opac-preview': 'rgba(248, 238, 238, 0.50)',
        'opac-sidebar' : 'rgba(255, 255, 255, 0.70)',
        'primary' : 'rgba(240, 89, 65, 1)',
        'primary-50': 'rgba(254, 242, 240, 1)',
        'primary-100': 'rgba(253, 232, 228, 1)',
        'primary-200': 'rgba(251, 209, 202, 1)',
        'primary-300': 'rgba(249, 177, 166, 1)',
        'primary-400': 'rgba(245, 133, 113, 1)',
        'primary-500': 'rgba(240, 89, 65, 1)',
        'primary-600': 'rgba(226, 65, 43, 1)',
        'primary-700': 'rgba(190, 49, 32, 1)',
        'primary-800': 'rgba(156, 44, 30, 1)',
        'primary-900': 'rgba(129, 42, 32, 1)',
        'primary-950': 'rgba(70, 19, 14, 1)',
        'secondary' : 'rgba(15, 1, 52, 1)',
        'secondary-800' : 'rgba(31, 2, 109, 0.8)',
        'graphite': 'rgba(65, 66, 76, 1)',
      },
      boxShadow : {
        'navbarShadow' : "0px 0px 2px 0px rgba(33, 33, 33, 0.15)",
        'min-shadow': '0px 0px 4px 0px rgba(0, 0, 0, 0.15)',
        'auth-box-shadow': '0px 30px 50px 0px rgba(0, 0, 0, 0.05), 0px 20px 24px 0px rgba(0, 0, 0, 0.05), 0px 0px 2px 0px rgba(33, 33, 33, 0.15)',
      },
      keyframes: {
        wiggle: {
          '25%': { transform: 'translateX(2px)' },
          '50%': { transform: 'translateX(-2px)' },
          '75%': { transform: 'translateX(2px)' },
          '100%': { transform: 'translateX(0)' },
        },
        slideInRight: {
          '0%': {
            transform: 'translateX(100%)',
            opacity: '0',
          },
          '100%': {
            transform: 'translateX(0)',
            opacity: '1',
          },
        },
        'fade-in-down': {
          '0%': {
            opacity: '0',
            transform: 'translateY(-10px)'
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)'
          },
        },
        wave1: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        wave2: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-15px)' },
        },
        wave3: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        'slide-up': {
          '0%': { transform: 'translate(-50%, 100%)', opacity: '0' },
          '100%': { transform: 'translate(-50%, 0)', opacity: '1' }
        }
      },
      animation: {
        wiggle: 'wiggle 0.3s ease-in-out',
        slideInRight: 'slideInRight 0.5s ease-out',
        'fade-in-down': 'fade-in-down 0.5s ease-out',
        wave1: 'wave1 1s ease-in-out infinite',
        wave2: 'wave2 1s ease-in-out infinite',
        wave3: 'wave3 1s ease-in-out infinite',
        'slide-up': 'slide-up 0.3s ease-out forwards'
      },
    },
  },
  plugins: [
    require('flowbite/plugin'),
    require('tailwind-scrollbar'),
    require("tailwindcss-animate"),
    require('@tailwindcss/typography'),
  ],
}

