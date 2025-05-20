/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',                 // Scans HTML files in DentalPrototype/templates/
    './appointments/templates/**/*.html',    // Scans HTML files in DentalPrototype/appointments/templates/
    // Add more paths here if you have templates in other Django apps, e.g.:
    // './other_app/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        // Your custom color palette
        'primary': '#2E7D32',       // Calm Leaf Green
        'secondary': '#A5D6A7',   // Soft Mint Green
        'accent': '#FFC107',        // Warm Amber
        'light-bg': '#F9FAFB',      // Near-white (used as bg-light-bg)
        'dark-bg': '#1E1E1E',       // Charcoal (used as bg-dark-bg)
        'text-light': '#212121',     // Dark Gray for text on light backgrounds
        'text-dark': '#E0E0E0',      // Light Gray for text on dark backgrounds
        'border-gray': '#BDBDBD',    // For borders
        'muted-text': '#757575',     // For less important text
      },
      fontFamily: {
        // Using Tailwind's default sans-serif stack is usually good.
        // You can override it here if you want to use specific fonts like Google Fonts.
        // 'sans': ['Inter', 'system-ui', 'sans-serif'], // Example with 'Inter'
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', "Segoe UI", 'Roboto', "Helvetica Neue", 'Arial', "Noto Sans", 'sans-serif', "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"],
      },
      borderRadius: {
        'base': '0.375rem', // 6px - for slightly rounded corners
        'sm': '0.25rem',   // 4px - for smaller elements
        // You can add 'lg', 'xl', 'full' etc. or keep Tailwind's defaults
      }
      // You can also extend spacing, boxShadow, etc. here if needed
    },
  },
  plugins: [
    require('@tailwindcss/forms'), // Optional: for nicer default form styling
                                   // If you use this, install it: npm install -D @tailwindcss/forms
  ],
}