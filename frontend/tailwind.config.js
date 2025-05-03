module.exports = {
  darkMode: 'class',
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './index.html',
    './src/index.css'         
  ],
  corePlugins: {
    // Disable Tailwind's preflight to avoid conflicts with Bootstrap
    preflight: false,
  },
  theme: {
    extend: {
      fontFamily: {
        sans: ['Figtree', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: {
          light: '#4F46E5', // Indigo 600
          DEFAULT: '#4338CA', // Indigo 700
          dark: '#3730A3',   // Indigo 800
        },
        gray: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          900: '#111827',
        },
      },
      borderRadius: {
        'xl': '0.75rem',  // Existing Tailwind value (12px)
        '2xl': '1rem',    // Existing Tailwind value (16px)
        '3xl': '1.5rem',  // 24px - For card components
        '4xl': '2rem',    // 32px - For even more rounded elements if needed
        'full': '9999px', // Already in Tailwind, used for fully rounded buttons
      },
      boxShadow: {
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
        none: 'none',
      },
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
      },
      transitionDuration: {
        '0': '0ms',
        '300': '300ms',
        '500': '500ms',
      },
      // Add table specific customizations
      tableLayout: {
        'fixed': 'fixed',
        'auto': 'auto',
      },
    },
  },
  plugins: [],
};