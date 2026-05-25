/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../templates/*.html',
    '../templates/**/*.html',
    '../**/templates/**/*.html',
    '../**/forms.py'
  ],
  theme: {
    backgroundColor: theam =>({
      ...theam.colors,
      'primary-900':'#FF8000',
      'primary-800':'#FF8C19',
      'primary-700':'#FF9933',
      'card-100':'#fef3c7',
      'card-200':'#fef397',
      'button-100':'#FF8000',
      'button-200':'#FF6000', 

    }),
    extend: {},
  },
  plugins: [],
}

