/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'cyber-dark': '#0a0e27',
        'cyber-darker': '#050810',
        'cyber-blue': '#0066ff',
        'cyber-cyan': '#00d9ff',
        'cyber-purple': '#8f00ff',
        'cyber-red': '#ff0055',
        'cyber-green': '#00ff41',
      },
      backgroundColor: {
        'glass': 'rgba(255, 255, 255, 0.05)',
      },
      borderColor: {
        'glass': 'rgba(255, 255, 255, 0.1)',
      },
      fontFamily: {
        'mono': ['Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
