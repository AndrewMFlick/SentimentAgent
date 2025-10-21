# Dashboard Component Contract

**Version**: 2.0.0 (TailwindCSS Migration)  
**Status**: Existing Component (Refactoring)  
**Breaking Changes**: None (internal styling only)

## Purpose

Main dashboard view displaying sentiment analytics, tool approvals, and trending topics.

## API Contract

### TypeScript Interface (UNCHANGED)

```typescript
// No props interface - Dashboard is a route component
export const Dashboard: React.FC = () => {
  // Component logic
};
```

**Migration Guarantee**: The Dashboard component has no props, so external API remains identical.

## Internal Changes (Style Migration)

### Before (Inline Styles)

```tsx
<div style={{
  backgroundColor: '#0a0a0a',
  minHeight: '100vh',
  padding: '32px'
}}>
  <div style={{
    backgroundColor: '#1a1a1a',
    padding: '24px',
    borderRadius: '12px',
    marginBottom: '24px'
  }}>
    {/* Content */}
  </div>
</div>
```

### After (TailwindCSS)

```tsx
<div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black p-8">
  <GlassCard variant="medium" className="p-6 mb-6">
    {/* Content */}
  </GlassCard>
</div>
```

## Component Structure

### Layout Hierarchy

```text
Dashboard (route)
├── Page Container (gradient background)
│   ├── Header Section
│   │   ├── Title
│   │   └── TimeRangeFilter
│   ├── Stats Grid
│   │   ├── GlassCard (Total Tools)
│   │   ├── GlassCard (Pending Approvals)
│   │   └── GlassCard (Average Sentiment)
│   ├── Charts Section
│   │   ├── GlassCard (Sentiment Over Time)
│   │   └── GlassCard (Tool Categories)
│   └── Tables Section
│       └── GlassCard (Recent Tools)
```

### Data Dependencies (UNCHANGED)

```typescript
// API calls remain identical
const { data: tools } = useQuery('/api/tools');
const { data: sentiment } = useQuery('/api/sentiment');
const { data: trending } = useQuery('/api/trending');
```

**Migration Guarantee**: All data fetching, state management, and business logic unchanged.

## Styling Contracts

### Color Palette

```typescript
// Background
'bg-gradient-to-br from-black via-gray-900 to-black'

// Glass cards
'bg-white/5 backdrop-blur-md border-white/10'

// Text hierarchy
'text-white'           // Headings
'text-gray-400'        // Body text
'text-gray-500'        // Secondary text

// Sentiment colors
'text-emerald-400'     // Positive
'text-red-400'         // Negative
'text-gray-400'        // Neutral
```

### Spacing & Layout

```typescript
// Page container
'container mx-auto px-4 py-8'

// Grid layout
'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'

// Card padding
'p-6'  // Standard card padding (24px)
'p-8'  // Large card padding (32px)
```

### Responsive Breakpoints

```typescript
// Mobile-first approach
'flex-col'           // Mobile: stack vertically
'md:flex-row'        // Tablet: horizontal layout
'lg:grid-cols-3'     // Desktop: 3-column grid
```

## Chart Integration

### Recharts Styling (Before)

```tsx
<LineChart>
  <Line 
    stroke="#10b981" 
    strokeWidth={2}
    style={{ filter: 'drop-shadow(0 0 4px rgba(16, 185, 129, 0.5))' }}
  />
</LineChart>
```

### Recharts Styling (After)

```tsx
<LineChart>
  <Line 
    stroke={chartColors.positive}
    strokeWidth={2}
    className="drop-shadow-[0_0_4px_rgba(16,185,129,0.5)]"
  />
</LineChart>
```

**Migration Guarantee**: Chart data, axes, and tooltips unchanged. Only visual styling enhanced.

## Accessibility (MAINTAINED)

### Keyboard Navigation

- All interactive elements remain keyboard accessible
- Tab order preserved
- Focus indicators enhanced with glass styling

### Screen Readers

```tsx
// Before and after (ARIA unchanged)
<section aria-label="Dashboard statistics">
  <h2>Statistics</h2>
  {/* Stats */}
</section>
```

### Color Contrast

- All text meets WCAG 2.1 AA standards
- White text on dark glass: 15:1 contrast ratio
- Sentiment colors: Minimum 4.5:1 contrast

## Testing Contract

### Unit Tests (UNCHANGED)

```typescript
describe('Dashboard', () => {
  it('renders without crashing', () => {});
  it('fetches and displays tools', () => {});
  it('filters by time range', () => {});
  it('displays sentiment charts', () => {});
});
```

**Migration Guarantee**: All existing tests pass without modification.

### Visual Regression Tests (NEW)

```typescript
describe('Dashboard Visual Regression', () => {
  it('matches screenshot on desktop', () => {});
  it('matches screenshot on tablet', () => {});
  it('matches screenshot on mobile', () => {});
  it('glass effects render correctly', () => {});
});
```

## Performance Contract

### Before Migration

- **Build Time**: ~20s
- **Initial Load**: ~2.5s
- **Bundle Size**: ~120KB CSS

### After Migration

- **Build Time**: ~25s (+5s for Tailwind compilation)
- **Initial Load**: ~2.5s (no change)
- **Bundle Size**: ~130KB CSS (+10KB Tailwind utilities)

**Migration Guarantee**: Performance degradation <10%, imperceptible to users.

## Migration Checklist

- [ ] Remove all `style={{}}` props from Dashboard.tsx
- [ ] Replace container `<div>` with `<GlassCard>` components
- [ ] Convert layout grids to Tailwind grid classes
- [ ] Update Recharts colors to use `chartColors` constants
- [ ] Add glass tooltip styling to Recharts
- [ ] Verify all existing tests pass
- [ ] Run visual regression tests
- [ ] Validate accessibility with Lighthouse
- [ ] Test responsive breakpoints (375px, 768px, 1024px, 1920px)

## Rollback Plan

If issues arise:

1. Revert `Dashboard.tsx` to previous commit
2. Reinstall old dependencies (no Tailwind)
3. All functionality restored (no data/API changes)

**Risk**: Low (component API unchanged, no external dependencies)

## Version History

- **1.0.0** (2024-12-15): Initial Dashboard component
- **2.0.0** (2025-01-15): TailwindCSS migration (no API changes)
