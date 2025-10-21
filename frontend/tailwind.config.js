/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Glass effect colors
        'glass-bg': 'rgba(255, 255, 255, 0.05)',
        'glass-bg-strong': 'rgba(255, 255, 255, 0.10)',
        'glass-border': 'rgba(255, 255, 255, 0.10)',
        'glass-border-strong': 'rgba(255, 255, 255, 0.20)',
        
        // Sentiment colors (semantic)
        'positive': '#10b981',  // Emerald-500
        'negative': '#ef4444',  // Red-500
        'neutral': '#6b7280',   // Gray-500
        'mixed': '#f59e0b',     // Amber-500
        
        // Functional colors
        'info': '#3b82f6',      // Blue-500
        'warning': '#f59e0b',   // Amber-500
        'success': '#10b981',   // Emerald-500
        'error': '#ef4444',     // Red-500
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 0, 0, 0.6)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
};
