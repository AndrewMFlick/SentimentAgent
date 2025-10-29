# Phase 5: Visual Design Guide - Time Range Selector

**Feature**: 017-pre-cached-sentiment | **Phase**: 5 | **Date**: October 29, 2025

---

## Overview

This guide demonstrates the visual design and user interaction for the multi-period time range selector in Phase 5.

---

## Component: TimeRangeFilter

**Location**: `frontend/src/components/TimeRangeFilter.tsx`  
**Design System**: Glass morphism with emerald accent colors

---

## Visual States

### 1. Default State (24h Selected)

```
┌─────────────────────────────────────────────────────────────────┐
│  Time Range                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Last 24 Hours │ │ Last 7 Days  │ │ Last 30 Days │            │
│  │      ✓        │ │              │ │              │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│   (Emerald bg)      (Glass bg)       (Glass bg)                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Color Legend:
- Selected (24h): bg-emerald-600 border-emerald-500 text-white
- Unselected: bg-dark-elevated/60 text-gray-200 hover:bg-dark-elevated/80
```

### 2. Hover State (7 Days Button)

```
┌─────────────────────────────────────────────────────────────────┐
│  Time Range                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Last 24 Hours │ │ Last 7 Days  │ │ Last 30 Days │            │
│  │      ✓        │ │    (hover)   │ │              │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│   (Emerald bg)      (Lighter bg)     (Glass bg)                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Hover Effect:
- Cursor: pointer
- Background: bg-dark-elevated/80 (slightly lighter)
- Transition: transition-all (smooth animation)
```

### 3. Active State (7 Days Selected)

```
┌─────────────────────────────────────────────────────────────────┐
│  Time Range                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Last 24 Hours │ │ Last 7 Days  │ │ Last 30 Days │            │
│  │              │ │      ✓        │ │              │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│   (Glass bg)        (Emerald bg)     (Glass bg)                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

State Change:
- Previous selection (24h) returns to glass background
- New selection (7d) gets emerald background
- Smooth transition between states
```

### 4. Active State (30 Days Selected)

```
┌─────────────────────────────────────────────────────────────────┐
│  Time Range                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Last 24 Hours │ │ Last 7 Days  │ │ Last 30 Days │            │
│  │              │ │              │ │      ✓        │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│   (Glass bg)        (Glass bg)       (Emerald bg)               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## User Interaction Flow

### Scenario 1: Switching from 24h to 7d

```
Step 1: Initial State
User sees dashboard with 24h data displayed
Time range selector shows "Last 24 Hours" in emerald

Step 2: User Hovers over "Last 7 Days"
Button background lightens (visual feedback)
Cursor changes to pointer

Step 3: User Clicks "Last 7 Days"
✓ Button state changes (emerald moves to 7d)
✓ API request sent with hours=168
✓ Loading indicator appears (optional)
✓ Sentiment data updates in <2s
✓ Chart animates to show new data

Step 4: Completion
Dashboard shows 7-day sentiment data
Time range selector shows "Last 7 Days" in emerald
User can now compare weekly trends
```

### Scenario 2: Switching from 7d to 30d

```
Step 1: Current State
Dashboard showing 7-day data
"Last 7 Days" button is emerald

Step 2: User Clicks "Last 30 Days"
✓ Button state changes (emerald moves to 30d)
✓ API request sent with hours=720
✓ Loading indicator (optional)
✓ Sentiment data updates in <2s
✓ Chart updates to show monthly trends

Step 3: Completion
Dashboard shows 30-day sentiment data
Larger dataset visible (more historical context)
User can analyze longer-term trends
```

---

## Integration with Dashboard

### Full Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Reddit Sentiment Analysis Dashboard                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Filters                                                         │
│  ┌──────────────────┐  ┌───────────────────────────────┐        │
│  │ Subreddit        │  │ Time Range                    │        │
│  │ ┌──────────────┐ │  │ ┌──────────┐ ┌──────────┐    │        │
│  │ │ All Subreddits│ │  │ │ Last 24h │ │ Last 7d  │    │        │
│  │ └──────────────┘ │  │ └──────────┘ └──────────┘    │        │
│  └──────────────────┘  │ ┌──────────┐ ┌──────────┐    │        │
│                        │ │ Last 30d │ │ Custom   │    │        │
│                        │ └──────────┘ └──────────┘    │        │
│                        └───────────────────────────────┘        │
│                                                                  │
│  AI Developer Tools Sentiment                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ GitHub       │ │ Cursor       │ │ Claude       │            │
│  │ Copilot      │ │              │ │              │            │
│  │              │ │              │ │              │            │
│  │ 😊 65%       │ │ 😊 72%       │ │ 😊 68%       │            │
│  │ 😐 20%       │ │ 😐 15%       │ │ 😐 22%       │            │
│  │ 😞 15%       │ │ 😞 13%       │ │ 😞 10%       │            │
│  │              │ │              │ │              │            │
│  │ 150 mentions │ │ 89 mentions  │ │ 103 mentions │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

When user changes time range:
1. All tool cards update simultaneously
2. Mention counts may increase (more data in longer periods)
3. Percentages may shift (different time windows)
4. Smooth transitions between states
```

---

## Component Styling Details

### CSS Classes

```css
/* Button Base */
.glass-button {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
  transition: all 0.2s ease;
}

/* Selected State */
.glass-button.selected {
  background: rgba(16, 185, 129, 0.4);  /* Emerald with transparency */
  border-color: rgba(16, 185, 129, 0.6);
  color: white;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
}

/* Hover State */
.glass-button:hover:not(.selected) {
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-1px);
}

/* Active State (clicking) */
.glass-button:active {
  transform: translateY(0);
}
```

### Responsive Design

**Desktop (lg: breakpoint)**
```
┌────────────────────────────────────────────────┐
│  Time Range                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 24 Hours │ │  7 Days  │ │ 30 Days  │       │
│  └──────────┘ └──────────┘ └──────────┘       │
└────────────────────────────────────────────────┘
```

**Tablet (md: breakpoint)**
```
┌─────────────────────────────────┐
│  Time Range                     │
│  ┌──────────┐ ┌──────────┐      │
│  │ 24 Hours │ │  7 Days  │      │
│  └──────────┘ └──────────┘      │
│  ┌──────────┐                   │
│  │ 30 Days  │                   │
│  └──────────┘                   │
└─────────────────────────────────┘
```

**Mobile (sm: breakpoint)**
```
┌──────────────────┐
│  Time Range      │
│  ┌────────────┐  │
│  │  24 Hours  │  │
│  └────────────┘  │
│  ┌────────────┐  │
│  │   7 Days   │  │
│  └────────────┘  │
│  ┌────────────┐  │
│  │  30 Days   │  │
│  └────────────┘  │
└──────────────────┘
```

---

## Performance Indicators

### Loading State (Optional Enhancement)

```
┌─────────────────────────────────────────────────────────────────┐
│  Time Range                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Last 24 Hours │ │ Last 7 Days  │ │ Last 30 Days │            │
│  │              │ │      ✓ ⏳     │ │              │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                     (Loading...)                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Loading indicator appears briefly while data loads
Typically <100ms for cache hit (barely visible)
May show for 1-2s on cache miss
```

### Cache Status Indicator (Future Enhancement)

```
┌─────────────────────────────────────────────────────────────────┐
│  Time Range                                     Cached ✓         │
├─────────────────────────────────────────────────────────────────┤
│  Data as of: 2 minutes ago                                      │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Last 24 Hours │ │ Last 7 Days  │ │ Last 30 Days │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘

Shows data freshness
Indicates cache status (cached vs on-demand)
User knows data recency
```

---

## Accessibility

### Keyboard Navigation

```
Tab Order:
1. Time Range Filter Component
   ↓ Tab
2. "Last 24 Hours" button (focus ring visible)
   ↓ Tab
3. "Last 7 Days" button (focus ring visible)
   ↓ Tab
4. "Last 30 Days" button (focus ring visible)
   ↓ Tab
5. Next component...

Activation:
- Enter/Space: Select focused time range
- Arrow Keys: Navigate between options (future enhancement)
```

### Screen Reader Support

```html
<button
  role="radio"
  aria-checked="true"
  aria-label="Filter by last 7 days"
  className="glass-button selected"
>
  Last 7 Days
</button>

Screen reader announces:
"Last 7 Days, radio button, checked"
```

---

## Data Flow Diagram

```
User Action: Click "Last 7 Days"
    ↓
Frontend: Update state (preset: '7d', hours: 168)
    ↓
React Query: Fetch tool sentiment with hours=168
    ↓
API Request: GET /api/v1/tools/{id}/sentiment?hours=168
    ↓
Backend: Cache Service
    ↓
Cache Lookup: sentiment_cache[tool_id:DAY_7]
    ↓
┌─────────────────┐
│ Cache Hit?      │
└─────────────────┘
    │
    ├─ YES → Return cached data (50-100ms)
    │         ↓
    │         Set is_cached=true
    │         ↓
    │         Return to frontend
    │
    └─ NO  → Calculate on-demand (1-3s)
              ↓
              Query sentiment_scores container
              ↓
              Aggregate data in Python
              ↓
              Save to cache (background)
              ↓
              Set is_cached=false
              ↓
              Return to frontend
    ↓
Frontend: Update UI
    ↓
Charts: Animate transition
    ↓
User: Sees updated sentiment data
```

---

## Color Palette

### Glass Morphism Colors

```css
/* Base Glass */
--glass-bg: rgba(255, 255, 255, 0.05)
--glass-border: rgba(255, 255, 255, 0.1)
--glass-hover: rgba(255, 255, 255, 0.08)

/* Emerald Accent (Selected) */
--emerald-600: #10b981
--emerald-500: #22c55e
--emerald-bg: rgba(16, 185, 129, 0.4)
--emerald-border: rgba(16, 185, 129, 0.6)
--emerald-shadow: rgba(16, 185, 129, 0.3)

/* Text Colors */
--text-white: #ffffff
--text-gray-200: #e5e7eb
--text-gray-300: #d1d5db
--text-gray-400: #9ca3af
```

### Sentiment Colors

```css
/* Positive */
--sentiment-positive: #10b981  /* Emerald */

/* Negative */
--sentiment-negative: #ef4444  /* Red */

/* Neutral */
--sentiment-neutral: #6b7280  /* Gray */
```

---

## Future Enhancements

### 1. Animation on Data Update

```
When time range changes:
1. Current data fades out (200ms)
2. Loading skeleton appears (optional)
3. New data fades in (300ms)
4. Chart bars/lines animate growth/shrinkage
5. Numbers count up/down to new values
```

### 2. Tooltip on Hover

```
┌──────────────┐
│ Last 7 Days  │ ← Hover triggers tooltip
└──────────────┘
       ↓
┌─────────────────────────┐
│ View sentiment from     │
│ the past 7 days         │
│ (168 hours)             │
│                         │
│ ⚡ Cached - Fast load   │
└─────────────────────────┘
```

### 3. Comparison Mode

```
┌─────────────────────────────────────────────────────────────────┐
│  Compare Time Ranges                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ☑ Last 7 Days     ☑ Last 30 Days                               │
│                                                                  │
│  [Show Comparison]                                               │
│                                                                  │
│  📊 GitHub Copilot                                               │
│  ┌────────────────────────────────────┐                         │
│  │  7 Days:  😊 65%  😞 15%           │                         │
│  │ 30 Days:  😊 68%  😞 12%  ▲ +3%    │                         │
│  └────────────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

The time range selector provides:
- ✅ Intuitive visual design (glass morphism)
- ✅ Clear active state (emerald accent)
- ✅ Smooth transitions
- ✅ Fast performance (<2s for all periods)
- ✅ Responsive layout (mobile-friendly)
- ✅ Accessibility support (keyboard + screen reader)
- ✅ Consistent with existing design system

Users can now easily switch between 1h, 24h, 7d, and 30d time periods to analyze AI developer tool sentiment trends over different time scales.
