/** @type {import('tailwindcss').Config} */
module.exports = {
  // Apenas o componente Tailwind entra no bundle.
  content: [
    './templates/components/question_header.html',
  ],
  darkMode: ['selector', '[data-bs-theme="dark"]'],
  // Escopa os utilitários para evitar colisões com o Bootstrap.
  important: '.question-header',
  corePlugins: {
    preflight: false,
  },
  theme: {
    fontFamily: {
      sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
    },
  },
  plugins: [],
};
