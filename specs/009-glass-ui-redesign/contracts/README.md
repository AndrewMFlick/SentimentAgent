# Component Contracts

This directory contains API contracts for all glass morphism components to ensure no breaking changes during the redesign.

## Contract Files

- `GlassCard.contract.md`: Glass card component props and behavior
- `GlassButton.contract.md`: Glass button variants and states
- `SentimentBadge.contract.md`: Sentiment indicator component
- `Dashboard.contract.md`: Dashboard component API (existing)
- `AdminToolApproval.contract.md`: Admin tool approval component API (existing)
- `ToolSentimentCard.contract.md`: Tool sentiment card component API (existing)
- `HotTopics.contract.md`: Hot topics component API (existing)
- `tailwind.config.contract.md`: TailwindCSS configuration contract

## Contract Principles

1. **No Breaking Changes**: All existing component props must remain backward compatible
2. **Additive Only**: New props can be added with sensible defaults
3. **Style Separation**: Inline `style` props removed, replaced with `className` composition
4. **Type Safety**: All TypeScript interfaces preserved or enhanced
5. **Accessibility**: ARIA attributes and keyboard navigation must be maintained

## Verification

Before merging:

- [ ] All existing unit tests pass without modification
- [ ] No TypeScript errors introduced
- [ ] All component APIs match contracts
- [ ] Visual regression tests pass
