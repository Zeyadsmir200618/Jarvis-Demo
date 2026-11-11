/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        jarvis: {
          900: "#090d16",
          800: "#0f172a",
          700: "#1e293b",
          600: "#334155",
          accent: "#38bdf8",
          glow: "rgba(56, 189, 248, 0.2)",
        }
      },
    },
  },
  plugins: [],
}
