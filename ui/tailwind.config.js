/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/Pages/**/*.elm", "./src/View.elm", "./src/Ui.elm"],
  theme: {
    colors: {
      gray: "#262626",
      white: "#ECDFBD",
      dark: "#1e0400",
      primary: "#582c2c",
      secondary: "#924a36",
      info: "#d06346",
      accent1: "#483b88",
      accent2: "#a8598a",
      accent3: "#68574c",
      accent4: "#58384c",
      success: "#279f1e",
      warning: "#f6c121",
      danger: "#ee114e",
      transparent: "#00000000",
    },
    fontFamily: {
      righteous: ["Righteous", "sans-serif"],
      josefin: ["Josefin Slab", "serif"],
      mitr: ["Mitr", "sans-serif"],
    },
    extend: {},
  },
  plugins: [],
};
