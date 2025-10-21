# Data Model: Glass UI Design System

**Phase 1** | **Status**: In Progress | **Date**: 2025-01-15

## Overview

This document defines the styling patterns, component library, and design tokens for the glass morphism design system. Since this is a UI redesign (no data persistence changes), the "data model" focuses on component styling patterns and the design token structure.

## Design Tokens

### Color Palette

```typescript
// tailwind.config.js - colors extension
export const colors = {
  // Backgrounds
  'bg-primary': '#000000',      // Pure black
  'bg-secondary': '#0a0a0a',    // Near black
  'bg-tertiary': '#1a1a1a',     // Dark gray
  
  // Glass Effects
  'glass-bg': 'rgba(255, 255, 255, 0.05)',      // Light glass background
  'glass-bg-strong': 'rgba(255, 255, 255, 0.10)', // Strong glass background
  'glass-border': 'rgba(255, 255, 255, 0.10)',  // Glass border
  'glass-border-strong': 'rgba(255, 255, 255, 0.20)', // Strong glass border
  
  // Sentiment Colors
  'positive': '#10b981',        // Emerald-500 (positive sentiment)
  'negative': '#ef4444',        // Red-500 (negative sentiment)
  'neutral': '#6b7280',         // Gray-500 (neutral sentiment)
  'mixed': '#f59e0b',           // Amber-500 (mixed sentiment)
  
  // Functional Colors
  'info': '#3b82f6',            // Blue-500 (informational)
  'warning': '#f59e0b',         // Amber-500 (warnings)
  'success': '#10b981',         // Emerald-500 (success states)
  'error': '#ef4444',           // Red-500 (errors)
  
  // Text Colors
  'text-primary': '#ffffff',    // White (primary text)
  'text-secondary': '#9ca3af',  // Gray-400 (secondary text)
  'text-tertiary': '#6b7280',   // Gray-500 (tertiary text)
};
```

### Typography

```typescript
// Font families (existing from current design)
const fontFamily = {
  sans: ['Inter', 'system-ui', 'sans-serif'],
  mono: ['Fira Code', 'monospace'],
};

// Font sizes
const fontSize = {
  'xs': '0.75rem',     // 12px
  'sm': '0.875rem',    // 14px
  'base': '1rem',      // 16px
  'lg': '1.125rem',    // 18px
  'xl': '1.25rem',     // 20px
  '2xl': '1.5rem',     // 24px
  '3xl': '1.875rem',   // 30px
  '4xl': '2.25rem',    // 36px
};

// Font weights
const fontWeight = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
};
```

### Spacing

```typescript
// Tailwind default spacing scale (0.25rem = 4px)
const spacing = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
};
```

### Border Radius

```typescript
const borderRadius = {
  none: '0',
  sm: '0.25rem',    // 4px
  DEFAULT: '0.5rem', // 8px
  md: '0.75rem',    // 12px
  lg: '1rem',       // 16px
  xl: '1.5rem',     // 24px
  '2xl': '2rem',    // 32px
  full: '9999px',   // Pills
};
```

### Shadows

```typescript
const boxShadow = {
  sm: '0 1px 2px rgba(0, 0, 0, 0.5)',
  DEFAULT: '0 4px 6px rgba(0, 0, 0, 0.5)',
  md: '0 6px 12px rgba(0, 0, 0, 0.5)',
  lg: '0 10px 20px rgba(0, 0, 0, 0.6)',
  xl: '0 15px 30px rgba(0, 0, 0, 0.7)',
  '2xl': '0 25px 50px rgba(0, 0, 0, 0.8)',
  glass: '0 8px 32px rgba(0, 0, 0, 0.6)',
};
```

### Backdrop Blur

```typescript
const backdropBlur = {
  none: '0',
  xs: '2px',
  sm: '4px',
  DEFAULT: '8px',
  md: '12px',
  lg: '16px',
  xl: '24px',
  '2xl': '40px',
};
```

## Component Styling Patterns

### Pattern 1: Glass Card

**Use Cases**: Dashboard cards, stat boxes, content containers

```tsx
<div className="glass-card p-6">
  {/* Content */}
</div>
```

**CSS Definition**:

```css
.glass-card {
  @apply bg-white/5 backdrop-blur-md border border-white/10 rounded-xl shadow-glass;
}
```

**Variants**:

```tsx
{/* Light glass */}
<div className="glass-card-light p-6">

{/* Strong glass */}
<div className="glass-card-strong p-6">

{/* Colored glass (positive sentiment) */}
<div className="glass-card bg-emerald-500/10 border-emerald-500/20">
```

### Pattern 2: Glass Button

**Use Cases**: Primary actions, filters, toggles

```tsx
<button className="glass-button">
  Action
</button>
```

**CSS Definition**:

```css
.glass-button {
  @apply bg-white/10 hover:bg-white/20 active:bg-white/30
         backdrop-blur-sm border border-white/20 hover:border-white/30
         rounded-lg px-4 py-2 
         transition-all duration-200
         text-white font-medium
         focus:outline-none focus:ring-2 focus:ring-emerald-500/50;
}
```

**Variants**:

```tsx
{/* Primary (emerald) */}
<button className="glass-button bg-emerald-500/20 border-emerald-500/50 hover:bg-emerald-500/30">

{/* Danger (red) */}
<button className="glass-button bg-red-500/20 border-red-500/50 hover:bg-red-500/30">

{/* Disabled */}
<button className="glass-button opacity-50 cursor-not-allowed" disabled>
```

### Pattern 3: Glass Input

**Use Cases**: Search, filters, form fields

```tsx
<input 
  className="glass-input" 
  placeholder="Search..."
/>
```

**CSS Definition**:

```css
.glass-input {
  @apply bg-black/50 backdrop-blur-sm 
         border border-white/20 
         rounded-lg px-4 py-2
         text-white placeholder-gray-400
         focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20
         transition-all duration-200;
}
```

### Pattern 4: Sentiment Indicator

**Use Cases**: Sentiment scores, trend indicators, badges

```tsx
<div className="sentiment-indicator sentiment-positive">
  +0.75
</div>
```

**CSS Definitions**:

```css
.sentiment-indicator {
  @apply inline-flex items-center gap-1.5 px-3 py-1.5 
         rounded-full text-sm font-semibold
         backdrop-blur-sm border;
}

.sentiment-positive {
  @apply bg-emerald-500/20 border-emerald-500/50 text-emerald-400;
}

.sentiment-negative {
  @apply bg-red-500/20 border-red-500/50 text-red-400;
}

.sentiment-neutral {
  @apply bg-gray-500/20 border-gray-500/50 text-gray-400;
}

.sentiment-mixed {
  @apply bg-amber-500/20 border-amber-500/50 text-amber-400;
}
```

### Pattern 5: Glass Modal/Dialog

**Use Cases**: Confirmation dialogs, detail views, settings

```tsx
<div className="glass-modal">
  <div className="glass-modal-content">
    {/* Modal content */}
  </div>
</div>
```

**CSS Definitions**:

```css
.glass-modal {
  @apply fixed inset-0 z-50 flex items-center justify-center
         bg-black/60 backdrop-blur-sm;
}

.glass-modal-content {
  @apply bg-black/90 backdrop-blur-xl 
         border border-white/20 
         rounded-2xl shadow-2xl
         max-w-2xl w-full mx-4
         p-8;
}
```

### Pattern 6: Glass Tooltip

**Use Cases**: Recharts tooltips, hover information

```tsx
<Tooltip 
  contentStyle={{
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '0.75rem',
    padding: '12px 16px',
  }}
  labelStyle={{ color: '#ffffff', fontWeight: 600 }}
  itemStyle={{ color: '#9ca3af' }}
/>
```

**Alternative** (custom React component):

```tsx
<div className="glass-tooltip">
  <div className="glass-tooltip-label">Jan 2025</div>
  <div className="glass-tooltip-item">
    <span className="text-emerald-400">●</span> Positive: 45
  </div>
</div>
```

```css
.glass-tooltip {
  @apply bg-black/90 backdrop-blur-md 
         border border-white/20 
         rounded-xl shadow-xl
         px-4 py-3 space-y-1;
}

.glass-tooltip-label {
  @apply text-white font-semibold text-sm;
}

.glass-tooltip-item {
  @apply text-gray-400 text-xs flex items-center gap-2;
}
```

## Component Library Structure

### Base Components

```typescript
// src/components/glass/GlassCard.tsx
interface GlassCardProps {
  variant?: 'light' | 'medium' | 'strong';
  className?: string;
  children: React.ReactNode;
}

export const GlassCard: React.FC<GlassCardProps> = ({ 
  variant = 'medium', 
  className = '', 
  children 
}) => {
  const variants = {
    light: 'bg-white/5 backdrop-blur-sm',
    medium: 'bg-white/5 backdrop-blur-md',
    strong: 'bg-white/10 backdrop-blur-lg',
  };
  
  return (
    <div className={`
      ${variants[variant]}
      border border-white/10 rounded-xl shadow-glass
      ${className}
    `}>
      {children}
    </div>
  );
};
```

```typescript
// src/components/glass/GlassButton.tsx
interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export const GlassButton: React.FC<GlassButtonProps> = ({ 
  variant = 'default',
  size = 'md',
  className = '',
  children,
  ...props
}) => {
  const variants = {
    default: 'bg-white/10 hover:bg-white/20 border-white/20',
    primary: 'bg-emerald-500/20 hover:bg-emerald-500/30 border-emerald-500/50',
    danger: 'bg-red-500/20 hover:bg-red-500/30 border-red-500/50',
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };
  
  return (
    <button 
      className={`
        ${variants[variant]}
        ${sizes[size]}
        backdrop-blur-sm border rounded-lg
        transition-all duration-200
        text-white font-medium
        focus:outline-none focus:ring-2 focus:ring-emerald-500/50
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
};
```

```typescript
// src/components/glass/SentimentBadge.tsx
interface SentimentBadgeProps {
  value: number; // -1 to 1
  showValue?: boolean;
}

export const SentimentBadge: React.FC<SentimentBadgeProps> = ({ 
  value, 
  showValue = true 
}) => {
  const getSentimentClass = () => {
    if (value > 0.2) return 'sentiment-positive';
    if (value < -0.2) return 'sentiment-negative';
    if (Math.abs(value) > 0.05) return 'sentiment-mixed';
    return 'sentiment-neutral';
  };
  
  const getSentimentLabel = () => {
    if (value > 0.2) return 'Positive';
    if (value < -0.2) return 'Negative';
    if (Math.abs(value) > 0.05) return 'Mixed';
    return 'Neutral';
  };
  
  return (
    <div className={`sentiment-indicator ${getSentimentClass()}`}>
      <span>{getSentimentLabel()}</span>
      {showValue && <span className="font-mono">{value.toFixed(2)}</span>}
    </div>
  );
};
```

## Recharts Theme Configuration

### Chart Color Scheme

```typescript
// src/components/charts/chartColors.ts
export const chartColors = {
  positive: '#10b981',      // Emerald-500
  negative: '#ef4444',      // Red-500
  neutral: '#6b7280',       // Gray-500
  mixed: '#f59e0b',         // Amber-500
  background: '#000000',    // Black
  gridLines: '#1a1a1a',     // Dark gray
  text: '#9ca3af',          // Gray-400
};

// For gradients
export const chartGradients = {
  positive: {
    start: { color: '#10b981', opacity: 0.8 },
    end: { color: '#10b981', opacity: 0 },
  },
  negative: {
    start: { color: '#ef4444', opacity: 0.8 },
    end: { color: '#ef4444', opacity: 0 },
  },
};
```

### Shared Chart Configuration

```typescript
// src/components/charts/chartConfig.ts
export const defaultChartConfig = {
  margin: { top: 10, right: 30, left: 0, bottom: 0 },
  cartesianGrid: {
    strokeDasharray: '3 3',
    stroke: chartColors.gridLines,
  },
  xAxis: {
    stroke: chartColors.text,
    tick: { fill: chartColors.text, fontSize: 12 },
  },
  yAxis: {
    stroke: chartColors.text,
    tick: { fill: chartColors.text, fontSize: 12 },
  },
  tooltip: {
    contentStyle: {
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(255, 255, 255, 0.2)',
      borderRadius: '0.75rem',
      padding: '12px 16px',
    },
    labelStyle: { color: '#ffffff', fontWeight: 600 },
    itemStyle: { color: '#9ca3af' },
  },
};
```

## Layout Patterns

### Dashboard Grid

```tsx
{/* Responsive grid layout */}
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <GlassCard>Stat 1</GlassCard>
  <GlassCard>Stat 2</GlassCard>
  <GlassCard>Stat 3</GlassCard>
</div>
```

### Page Container

```tsx
<div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black">
  <div className="container mx-auto px-4 py-8">
    {/* Page content */}
  </div>
</div>
```

### Sidebar Layout (if needed)

```tsx
<div className="flex h-screen">
  {/* Sidebar */}
  <aside className="w-64 bg-black/50 backdrop-blur-md border-r border-white/10">
    {/* Navigation */}
  </aside>
  
  {/* Main content */}
  <main className="flex-1 overflow-y-auto bg-gradient-to-br from-black to-gray-900">
    {/* Content */}
  </main>
</div>
```

## Animation Patterns

### Transition Utilities

```tsx
{/* Smooth all properties */}
<div className="transition-all duration-200">

{/* Specific properties (better performance) */}
<div className="transition-transform duration-300 hover:scale-105">
<div className="transition-opacity duration-200 hover:opacity-80">

{/* Staggered animations (for lists) */}
<div className="animate-fadeIn" style={{ animationDelay: '100ms' }}>
```

### Custom Animations (tailwind.config.js)

```javascript
{
  theme: {
    extend: {
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.5s ease-out',
        shimmer: 'shimmer 2s infinite',
      },
    },
  },
}
```

## Responsive Design Strategy

### Mobile-First Breakpoints

```tsx
{/* Mobile (default) */}
<div className="p-4 text-sm">

{/* Tablet (768px+) */}
<div className="p-4 md:p-6 text-sm md:text-base">

{/* Desktop (1024px+) */}
<div className="p-4 md:p-6 lg:p-8 text-sm md:text-base lg:text-lg">
```

### Glass Effect Scaling

```tsx
{/* Lighter glass on mobile for performance */}
<div className="backdrop-blur-sm md:backdrop-blur-md lg:backdrop-blur-lg">
```

## Accessibility Considerations

### Contrast Compliance

All text on glass backgrounds must meet WCAG 2.1 AA:

- **White on dark glass**: `text-white` (always passes)
- **Colored text**: Use `text-{color}-400` or lighter for sufficient contrast
- **Focus states**: Always include `focus:ring-2 focus:ring-{color}/50`

### Keyboard Navigation

```tsx
<button className="
  focus:outline-none 
  focus:ring-2 focus:ring-emerald-500/50 
  focus:ring-offset-2 focus:ring-offset-black
">
```

### Screen Reader Support

```tsx
<div 
  className="sentiment-indicator sentiment-positive"
  role="status"
  aria-label="Positive sentiment: 0.75"
>
  +0.75
</div>
```

## Next Steps

**Phase 2 Deliverables**:

1. `contracts/`: Component prop interfaces, API contracts
2. `quickstart.md`: Development setup guide
3. `tasks.md`: Implementation task breakdown
4. Update `.github/copilot-instructions.md` with TailwindCSS patterns

**Ready to Proceed**: ✅ Yes - Design system complete, patterns validated.
