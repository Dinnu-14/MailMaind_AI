/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Manrope", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#eef1ff", 100: "#e0e5ff", 200: "#c4ccff", 300: "#9aa7fb", 400: "#6e7cf0",
          500: "#4a5be0", 600: "#3347d1", 700: "#2937ae", 800: "#243088", 900: "#1f296b",
        },
      },
      keyframes: {
        slidein: { from: { transform: "translateX(24px)", opacity: "0" }, to: { transform: "none", opacity: "1" } },
        pop: { from: { transform: "translateY(6px)", opacity: "0" }, to: { transform: "none", opacity: "1" } },
      },
      animation: { slidein: "slidein .22s ease-out", pop: "pop .18s ease-out" },
    },
  },
  plugins: [],
};
