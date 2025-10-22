# Phase 5: Archive/Unarchive Tools - Visual Guide

## UI Components Overview

This document provides a visual description of the archive/unarchive UI components added in Phase 5.

## 1. ToolTable - Active Tools View

### Archive Button Display
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Tool Name          │ Vendor    │ Category        │ Status  │ Actions   │
├─────────────────────────────────────────────────────────────────────────┤
│ GitHub Copilot     │ GitHub    │ [Code Assistant]│ Active  │ ✏️ Edit    │
│ AI-powered coding  │           │                 │         │ 📦 Archive │
│                    │           │                 │         │ 🗑️ Delete  │
└─────────────────────────────────────────────────────────────────────────┘
```

**Button Colors**:
- ✏️ Edit: Blue theme (`bg-blue-900/40 border-blue-700/50`)
- 📦 Archive: Yellow theme (`bg-yellow-900/40 border-yellow-700/50`)
- 🗑️ Delete: Red theme (`bg-red-900/40 border-red-700/50`)

## 2. ToolTable - Archived Tools View

### Unarchive Button Display
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Tool Name          │ Vendor    │ Category        │ Status   │ Actions  │
├─────────────────────────────────────────────────────────────────────────┤
│ Legacy Tool        │ Vendor X  │ [Code Review]   │ Archived │ ✏️ Edit   │
│ Old deprecated tool│           │                 │          │ ↩️ Unarch │
│                    │           │                 │          │ 🗑️ Delete │
└─────────────────────────────────────────────────────────────────────────┘
```

**Status Badge**:
- Active: Green (`bg-emerald-900/40 border-emerald-700/50 text-emerald-300`)
- Archived: Gray (`bg-gray-900/40 border-gray-700/50 text-gray-300`)

**Button Colors**:
- ↩️ Unarchive: Green theme (`bg-emerald-900/40 border-emerald-700/50`)

## 3. ArchiveConfirmationDialog

### Modal Layout
```
┌───────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────┐  │
│  │ 📦  Archive Tool                               │  │
│  │                                                 │  │
│  │ Are you sure you want to archive                │  │
│  │ "GitHub Copilot"?                               │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Archiving this tool will:                       │  │
│  │ • Remove it from the active tools list          │  │
│  │ • Preserve all historical sentiment data        │  │
│  │ • Allow you to restore it later if needed       │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Archive Tool    │  │     Cancel       │          │
│  └──────────────────┘  └──────────────────┘          │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Modal Features**:
- Glass-themed background (`glass-card` class)
- 📦 emoji icon for visual clarity
- Informative bullet points explaining the action
- Yellow Archive button (`bg-yellow-900/40`)
- Standard Cancel button

### Error State
```
┌───────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────┐  │
│  │ 📦  Archive Tool                               │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ⚠️ Error: Cannot archive tool: 2 tool(s) were  │  │
│  │ merged into this tool (Tool A, Tool B). Please  │  │
│  │ unmerge or archive those tools first.           │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  [Error displayed in red theme]                       │
└────────────────────────────────────────────────────────┘
```

## 4. Success Notification

### Archive Success
```
┌─────────────────────────────────────────────────┐
│ ✓ Tool has been archived successfully          │
└─────────────────────────────────────────────────┘
```
- Green theme (`bg-emerald-500/10 border-emerald-500/20 text-emerald-400`)
- Auto-dismisses after 3 seconds

### Unarchive Success
```
┌─────────────────────────────────────────────────┐
│ ✓ Tool "GitHub Copilot" has been unarchived    │
│   successfully                                  │
└─────────────────────────────────────────────────┘
```

## 5. Filter Integration

### Status Filter Dropdown
```
┌────────────────────────────┐
│ Status: [Active ▼]         │
└────────────────────────────┘
  ↓
┌────────────────────────────┐
│ • All                      │
│ ✓ Active                   │
│ • Archived                 │
└────────────────────────────┘
```

**Filter Behavior**:
- Default: Shows only active tools
- "Active": Shows tools with status='active', Archive button visible
- "Archived": Shows tools with status='archived', Unarchive button visible
- "All": Shows both active and archived tools, appropriate buttons shown

## 6. User Flows

### Archive Flow
```
1. [Active Tool List]
   ↓
2. Click "📦 Archive" button
   ↓
3. [ArchiveConfirmationDialog opens]
   ↓
4. Click "Archive Tool"
   ↓
5. [Loading spinner: "Archiving..."]
   ↓
6. [Success notification: "✓ Tool has been archived successfully"]
   ↓
7. [Table refreshes, tool no longer in active list]
   ↓
8. Change filter to "Archived" to see the tool
```

### Unarchive Flow
```
1. Set filter to "Archived"
   ↓
2. [Archived Tool List]
   ↓
3. Click "↩️ Unarchive" button
   ↓
4. [Direct API call, no confirmation]
   ↓
5. [Success notification: "✓ Tool "Name" has been unarchived successfully"]
   ↓
6. [Table refreshes, tool back in active list]
   ↓
7. Change filter to "Active" to see the tool
```

### Error Handling Flow
```
1. Click "📦 Archive" on tool with merged references
   ↓
2. [ArchiveConfirmationDialog opens]
   ↓
3. Click "Archive Tool"
   ↓
4. [API returns 409 Conflict]
   ↓
5. [Error message in dialog: Shows which tools block archive]
   ↓
6. User can:
   - Click Cancel to close dialog
   - Go archive the blocking tools first
```

## 7. Responsive Design

### Desktop View (≥768px)
- All buttons displayed in a horizontal row
- Full button text visible
- Comfortable spacing between buttons

### Mobile View (<768px)
- Buttons may wrap to multiple lines
- Icons remain visible for clarity
- Touch-friendly button sizing

## 8. Accessibility Features

- **Keyboard Navigation**: All buttons are keyboard accessible
- **Screen Readers**: Buttons have `title` attributes
- **Focus Indicators**: Visible focus rings on all interactive elements
- **Color Contrast**: WCAG 2.1 AA compliant contrast ratios
- **Error Messages**: Clear, descriptive error text

## 9. Theme Consistency

All components follow the glass morphism design system:

```css
/* Glass Card */
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

/* Glass Button */
.glass-button {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  transition: all 0.2s;
}

.glass-button:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.3);
}
```

## 10. Loading States

### Archive Operation Loading
```
┌───────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────┐  │
│  │ 📦  Archive Tool                               │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Archiving... ⏳ │  │  Cancel (disabled)│          │
│  └──────────────────┘  └──────────────────┘          │
└────────────────────────────────────────────────────────┘
```

### Table Refresh Loading
```
┌────────────────────────────────────────────┐
│  Loading overlay with spinner...          │
│  "Updating tools..."                       │
└────────────────────────────────────────────┘
```

## Implementation Notes

1. **Conditional Rendering**: Archive/Unarchive buttons show based on `tool.status`
2. **State Management**: React Query handles caching and invalidation
3. **Error Boundaries**: Errors caught and displayed user-friendly
4. **Performance**: Debounced searches, paginated results
5. **Security**: All operations require admin authentication

## Testing Checklist

Visual Testing:
- [ ] Archive button appears for active tools
- [ ] Unarchive button appears for archived tools
- [ ] ArchiveConfirmationDialog displays correctly
- [ ] Success notifications show and auto-dismiss
- [ ] Error messages display in red theme
- [ ] Glass theme consistent across all components
- [ ] Buttons have correct colors and icons
- [ ] Loading states show during operations
- [ ] Mobile responsive layout works

Functional Testing:
- [ ] Archive button opens confirmation dialog
- [ ] Confirmation dialog Archive button works
- [ ] Cancel button closes dialog without action
- [ ] Unarchive button works without confirmation
- [ ] Success messages show tool name
- [ ] Error messages are clear and actionable
- [ ] Table refreshes after operations
- [ ] Filter shows correct tools by status
