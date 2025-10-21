/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable dark mode with class strategy
  theme: {
    extend: {
      colors: {
        // Dark mode backgrounds
        'dark-bg': '#0a0a0a',        // Near black background
        'dark-surface': '#1a1a1a',   // Dark surface
        'dark-elevated': '#2a2a2a',  // Elevated surface
        
        // Glass effect colors (darker for dark mode)
        'glass-bg': 'rgba(20, 20, 20, 0.6)',          // Dark glass background
        'glass-bg-strong': 'rgba(30, 30, 30, 0.8)',   // Strong dark glass
        'glass-border': 'rgba(255, 255, 255, 0.08)',  // Subtle border
        'glass-border-strong': 'rgba(255, 255, 255, 0.15)', // Stronger border
        
        // Sentiment colors (optimized for dark mode)
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
        'glass': '0 8px 32px rgba(0, 0, 0, 0.8)',
        'glass-sm': '0 4px 16px rgba(0, 0, 0, 0.6)',
      },
      backdropBlur: {
        xs: '2px',
      },
      backgroundImage: {
        'gradient-dark': 'linear-gradient(to bottom right, #000000, #0a0a0a, #1a1a1a)',
        'gradient-dark-radial': 'radial-gradient(circle at top right, #1a1a1a, #000000)',
      },
    },
  },
  plugins: [],
};
