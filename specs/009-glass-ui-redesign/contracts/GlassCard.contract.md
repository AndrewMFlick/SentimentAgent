# GlassCard Component Contract

**Version**: 1.0.0  
**Status**: New Component  
**Breaking Changes**: None (new component)

## Purpose

Reusable glass morphism card component for dashboard stats, content containers, and data displays.

## API Contract

### TypeScript Interface

```typescript
interface GlassCardProps {
  /**
   * Glass effect intensity
   * @default 'medium'
   */
  variant?: 'light' | 'medium' | 'strong';
  
  /**
   * Additional Tailwind classes to apply
   * @default ''
   */
  className?: string;
  
  /**
   * Card content
   */
  children: React.ReactNode;
  
  /**
   * Optional click handler
   */
  onClick?: () => void;
  
  /**
   * Hover effect enabled
   * @default false
   */
  hoverable?: boolean;
}
```

### Props Behavior

| Prop | Type | Default | Description | Example |
|------|------|---------|-------------|---------|
| `variant` | `'light' \| 'medium' \| 'strong'` | `'medium'` | Controls backdrop-blur intensity | `variant="strong"` |
| `className` | `string` | `''` | Additional Tailwind classes | `className="p-6"` |
| `children` | `ReactNode` | Required | Card content | `<GlassCard>Content</GlassCard>` |
| `onClick` | `() => void` | `undefined` | Click handler (makes card interactive) | `onClick={() => alert('Clicked')}` |
| `hoverable` | `boolean` | `false` | Adds hover scaling effect | `hoverable={true}` |

### CSS Classes Applied

```tsx
// Base classes (always applied)
'border border-white/10 rounded-xl shadow-glass'

// Variant classes (based on variant prop)
variant === 'light': 'bg-white/5 backdrop-blur-sm'
variant === 'medium': 'bg-white/5 backdrop-blur-md'
variant === 'strong': 'bg-white/10 backdrop-blur-lg'

// Interactive classes (when onClick provided)
onClick !== undefined: 'cursor-pointer hover:border-white/20 transition-all duration-200'

// Hoverable classes (when hoverable=true)
hoverable === true: 'hover:scale-[1.02] transition-transform duration-200'
```

### Usage Examples

```tsx
// Basic card
<GlassCard className="p-6">
  <h3 className="text-lg font-semibold text-white">Title</h3>
  <p className="text-gray-400">Description</p>
</GlassCard>

// Strong glass with padding
<GlassCard variant="strong" className="p-8">
  <StatDisplay value={1234} label="Total Tools" />
</GlassCard>

// Interactive card
<GlassCard 
  onClick={() => navigate('/details')}
  hoverable={true}
  className="p-4"
>
  Click me!
</GlassCard>

// Light glass (subtle)
<GlassCard variant="light" className="p-3 text-sm">
  Subtle info box
</GlassCard>
```

## Accessibility

### ARIA Attributes

```tsx
// When onClick is provided
<div role="button" tabIndex={0} onKeyPress={handleKeyPress}>

// When onClick is NOT provided
<div role="article">
```

### Keyboard Navigation

- **Enter/Space**: Trigger `onClick` handler (when interactive)
- **Tab**: Focus next interactive element
- **Shift+Tab**: Focus previous interactive element

### Focus States

```css
focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:ring-offset-2 focus:ring-offset-black
```

## Testing Contract

### Unit Tests Required

```typescript
describe('GlassCard', () => {
  it('renders children correctly', () => {});
  it('applies variant classes correctly', () => {});
  it('applies custom className', () => {});
  it('calls onClick when clicked', () => {});
  it('adds hover effect when hoverable=true', () => {});
  it('supports keyboard navigation when interactive', () => {});
});
```

### Visual Regression Tests

- Light variant rendering
- Medium variant rendering (default)
- Strong variant rendering
- Hover state (when hoverable)
- Focus state (when interactive)

## Migration Notes

**Current Pattern** (inline styles):

```tsx
<div style={{
  backgroundColor: 'rgba(26, 26, 26, 0.8)',
  padding: '24px',
  borderRadius: '12px',
  boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
}}>
  Content
</div>
```

**New Pattern** (GlassCard):

```tsx
<GlassCard variant="medium" className="p-6">
  Content
</GlassCard>
```

**Benefits**:

- No inline styles (fixes CSS linting errors)
- Consistent glass effect across app
- Easier to maintain and update
- Better TypeScript type safety

## Version History

- **1.0.0** (2025-01-15): Initial contract
