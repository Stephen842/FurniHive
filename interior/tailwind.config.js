/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
     './furniture/templates/pages/*.html',
  ],
  theme: {
    extend: {
      fontFamily: {
        baloo: ["Baloo 2", "cursive"],
      },
    },
  },
  plugins: [],
}
