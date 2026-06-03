/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        cream: "#F8F6EC",
        surface: "#FFFDF5",
        forest: "#123524",
        leaf: "#1F7A43",
        sage: "#E8F3E8",
        line: "#D8E8D2",
      },
      boxShadow: {
        soft: "0 18px 60px rgba(31, 42, 36, 0.10)",
      },
    },
  },
  plugins: [],
};
