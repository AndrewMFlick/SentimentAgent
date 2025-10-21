# Quickstart: Glass UI Development

**Feature**: 009-glass-ui-redesign  
**Last Updated**: 2025-01-15

## Prerequisites

- Node.js 18+ and npm 9+
- VS Code with ESLint and Tailwind CSS IntelliSense extensions
- Basic familiarity with React and TailwindCSS

## Initial Setup (One-Time)

### 1. Install Dependencies

```bash
cd frontend
npm install -D tailwindcss@^3.4.1 postcss@^8.4.35 autoprefixer@^10.4.17
```

### 2. Initialize TailwindCSS

```bash
npx tailwindcss init -p
```

This creates:

- `tailwind.config.js`: Tailwind configuration
- `postcss.config.js`: PostCSS configuration

### 3. Configure Tailwind

Edit `frontend/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'glass-bg': 'rgba(255, 255, 255, 0.05)',
        'glass-border': 'rgba(255, 255, 255, 0.1)',
        'positive': '#10b981',
        'negative': '#ef4444',
        'neutral': '#6b7280',
        'info': '#3b82f6',
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
```

### 4. Add Tailwind Directives

Edit `frontend/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom glass utilities */
@layer components {
  .glass-card {
    @apply bg-white/5 backdrop-blur-md border border-white/10 rounded-xl shadow-glass;
  }
  
  .glass-button {
    @apply bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 
           rounded-lg px-4 py-2 transition-all duration-200
           text-white font-medium
           focus:outline-none focus:ring-2 focus:ring-emerald-500/50;
  }
  
  .glass-input {
    @apply bg-black/50 backdrop-blur-sm border border-white/20 rounded-lg px-4 py-2
           text-white placeholder-gray-400
           focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20
           transition-all duration-200;
  }
  
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
}
```

### 5. Install VS Code Extensions

Install these extensions for better DX:

- **Tailwind CSS IntelliSense** (`bradlc.vscode-tailwindcss`): Autocomplete, linting, hover preview
- **ESLint** (`dbaeumer.vscode-eslint`): JavaScript/TypeScript linting
- **Prettier** (`esbenp.prettier-vscode`): Code formatting

### 6. Verify Setup

```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` and verify the app loads. You should see the existing UI (no changes yet).

## Development Workflow

### Starting Development Server

```bash
cd frontend
npm run dev
```

The dev server runs on `http://localhost:5173` with hot module replacement (HMR).

### Converting Components to Tailwind

#### Step 1: Identify Inline Styles

Search for `style={{` in your component:

```tsx
// Before
<div style={{
  backgroundColor: '#1a1a1a',
  padding: '24px',
  borderRadius: '12px',
}}>
  Content
</div>
```

#### Step 2: Convert to Tailwind Classes

Replace inline styles with Tailwind utilities:

```tsx
// After
<div className="bg-gray-900 p-6 rounded-xl">
  Content
</div>
```

#### Step 3: Use Glass Components

For cards, use the `glass-card` utility:

```tsx
// Better
<div className="glass-card p-6">
  Content
</div>
```

Or use the `GlassCard` component (once created):

```tsx
// Best
<GlassCard variant="medium" className="p-6">
  Content
</GlassCard>
```

### Common Conversion Patterns

#### Background Colors

```tsx
// Before
style={{ backgroundColor: '#1a1a1a' }}

// After
className="bg-gray-900"

// Glass variant
className="bg-white/5 backdrop-blur-md"
```

#### Padding & Margin

```tsx
// Before
style={{ padding: '24px', margin: '16px 0' }}

// After
className="p-6 my-4"
```

**Tailwind Spacing Scale**: `1` = 4px, `2` = 8px, `3` = 12px, `4` = 16px, `6` = 24px, `8` = 32px

#### Border Radius

```tsx
// Before
style={{ borderRadius: '12px' }}

// After
className="rounded-xl"
```

**Tailwind Border Radius**: `rounded-sm` (4px), `rounded` (8px), `rounded-lg` (12px), `rounded-xl` (16px)

#### Flexbox & Grid

```tsx
// Before
style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}

// After
className="flex flex-col gap-4"
```

```tsx
// Before
style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}

// After
className="grid grid-cols-3 gap-6"
```

#### Hover States

```tsx
// Before
<button 
  style={{ backgroundColor: isHovered ? '#2a2a2a' : '#1a1a1a' }}
  onMouseEnter={() => setIsHovered(true)}
  onMouseLeave={() => setIsHovered(false)}
>

// After
<button className="bg-gray-900 hover:bg-gray-800 transition-colors duration-200">
```

### Using Glass Utilities

#### Glass Card

```tsx
<div className="glass-card p-6">
  <h3 className="text-lg font-semibold text-white">Card Title</h3>
  <p className="text-gray-400">Card description</p>
</div>
```

#### Glass Button

```tsx
<button className="glass-button">
  Click Me
</button>

{/* Primary variant */}
<button className="glass-button bg-emerald-500/20 border-emerald-500/50 hover:bg-emerald-500/30">
  Primary Action
</button>
```

#### Sentiment Indicator

```tsx
<span className="sentiment-indicator sentiment-positive">
  Positive
</span>

<span className="sentiment-indicator sentiment-negative">
  Negative
</span>
```

### Recharts Integration

#### Chart Container

```tsx
<div className="glass-card p-6">
  <h3 className="text-white font-semibold mb-4">Sentiment Over Time</h3>
  <ResponsiveContainer width="100%" height={300}>
    <LineChart data={data}>
      <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
      <XAxis stroke="#9ca3af" tick={{ fill: '#9ca3af' }} />
      <YAxis stroke="#9ca3af" tick={{ fill: '#9ca3af' }} />
      <Tooltip 
        contentStyle={{
          backgroundColor: 'rgba(0, 0, 0, 0.9)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: '0.75rem',
        }}
      />
      <Line 
        type="monotone" 
        dataKey="sentiment" 
        stroke="#10b981" 
        strokeWidth={2}
      />
    </LineChart>
  </ResponsiveContainer>
</div>
```

## Testing

### Visual Testing

1. **Desktop View** (1920x1080):

   ```bash
   npm run dev
   # Open http://localhost:5173 in Chrome
   # Verify glass effects, layouts, colors
   ```

2. **Tablet View** (768x1024):

   - Open Chrome DevTools (F12)
   - Click device toolbar (Ctrl+Shift+M)
   - Select "iPad" preset
   - Verify responsive layout

3. **Mobile View** (375x667):
   - Select "iPhone SE" preset
   - Verify mobile layout, touch targets

### Accessibility Testing

Run Lighthouse in Chrome DevTools:

```text
1. Open Chrome DevTools (F12)
2. Click "Lighthouse" tab
3. Check "Accessibility"
4. Click "Analyze page load"
5. Verify score >= 95
```

Check color contrast:

- All text on glass backgrounds must meet WCAG 2.1 AA (4.5:1 ratio)
- Use white text (`text-white`) on dark glass
- Verify with Chrome DevTools "Accessibility" pane

### Automated Testing

Run existing tests:

```bash
cd frontend
npm run test
```

All existing tests should pass without modification.

## Troubleshooting

### Issue: Tailwind classes not working

**Solution**: Verify `content` paths in `tailwind.config.js`:

```javascript
content: [
  "./index.html",
  "./src/**/*.{js,ts,jsx,tsx}",  // Must include all file types
],
```

Restart dev server:

```bash
npm run dev
```

### Issue: Backdrop-filter not visible

**Solution**: Check browser support. Backdrop-filter requires:

- Chrome 76+
- Firefox 103+
- Safari 9+
- Edge 79+

Test in Chrome first. For older browsers, fallback is solid background:

```css
@supports not (backdrop-filter: blur(1px)) {
  .glass-card {
    background-color: rgba(0, 0, 0, 0.85);
  }
}
```

### Issue: CSS inline style warnings still present

**Solution**: Remove ALL `style={{}}` props. Search for:

```bash
grep -r "style={{" src/
```

Replace each occurrence with Tailwind classes.

### Issue: Build time too slow

**Solution**: Ensure Tailwind content paths are specific:

```javascript
// Good (specific)
content: ["./src/**/*.{ts,tsx}"],

// Bad (too broad)
content: ["./**/*"],
```

Also enable JIT mode (enabled by default in Tailwind 3.x).

### Issue: Colors not matching design

**Solution**: Use custom colors from `tailwind.config.js`:

```tsx
<div className="bg-positive/20">  {/* Custom emerald */}
<div className="text-negative">   {/* Custom red */}
```

Or use Tailwind's palette:

```tsx
<div className="bg-emerald-500/20">
<div className="text-red-400">
```

## Useful Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Lint code
npm run lint

# Format code
npm run format
```

## VS Code Shortcuts

- **Ctrl+Space**: Trigger Tailwind autocomplete
- **Hover**: Preview Tailwind class (color, spacing, etc.)
- **F2**: Rename component/variable
- **Ctrl+Shift+F**: Search across all files

## Resources

- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [Tailwind Play (Online Playground)](https://play.tailwindcss.com/)
- [Recharts Documentation](https://recharts.org/)
- [Glassmorphism CSS Generator](https://glassmorphism.com/)
- [WCAG Contrast Checker](https://webaim.org/resources/contrastchecker/)

## Next Steps

1. **Read Contracts**: Review `contracts/` directory for component API guarantees
2. **Study Patterns**: Check `data-model.md` for component styling patterns
3. **Start Converting**: Begin with `Dashboard.tsx` (largest component)
4. **Test Continuously**: Run visual regression tests after each component
5. **Ask Questions**: If stuck, check `research.md` or ask in team chat

Happy coding! 🚀
