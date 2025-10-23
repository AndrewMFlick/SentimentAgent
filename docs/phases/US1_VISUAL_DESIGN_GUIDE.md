# Hot Topics Dashboard - Visual Design Guide

## Page Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  Navigation Bar (Glass Card - Strong)                                 │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Reddit Sentiment Analysis     [Dashboard] [Hot Topics] [Admin] │  │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  Hot Topics Page                                                       │
│                                                                        │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓    │
│  ┃  Hot Topics                                                   ┃    │
│  ┃  Trending developer tools ranked by engagement and sentiment ┃    │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛    │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  [Last 24 Hours]  [Last 7 Days ●]  [Last 30 Days]            │    │
│  │                              Generated: 5:30 PM • Updating... │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  #1  GitHub Copilot                        ║ EMERALD BORDER   │  │
│  │                                             ║                  │  │
│  │  ┌──────────────┬──────────────┬──────────────┬──────────────┐│  │
│  │  │ Engagement   │ Mentions     │ Comments     │ Upvotes      ││  │
│  │  │ Score        │              │              │              ││  │
│  │  │ 1,250        │ 25           │ 480          │ 310          ││  │
│  │  └──────────────┴──────────────┴──────────────┴──────────────┘│  │
│  │                                                                │  │
│  │  Sentiment Distribution                                        │  │
│  │  🟢 72.0% (18)   🔴 16.0% (4)   ⚪ 12.0% (3)                   │  │
│  │  [████████████████──────]                                      │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  #2  ChatGPT                                ║ EMERALD BORDER   │  │
│  │                                             ║                  │  │
│  │  Engagement Score: 980 | Mentions: 18 | Comments: 320 | ...   │  │
│  │  🟢 68.5% (12)   🔴 22.2% (4)   ⚪ 9.3% (2)                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  #3  Claude                                 ║ AMBER BORDER     │  │
│  │                                             ║                  │  │
│  │  Engagement Score: 720 | Mentions: 12 | Comments: 240 | ...   │  │
│  │  🟢 45.0% (5)   🔴 35.0% (4)   ⚪ 20.0% (3)                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ... more hot topics ...                                              │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

## Color Palette

### Glass Morphism
- Background: `rgba(255, 255, 255, 0.05)` - 5% white
- Backdrop blur: `blur(12px)`
- Border: `rgba(255, 255, 255, 0.1)` - 10% white

### Sentiment Colors
- **Positive** (Emerald): `#10b981` (emerald-500)
- **Negative** (Red): `#ef4444` (red-500)
- **Neutral** (Gray): `#6b7280` (gray-500)
- **Mixed** (Amber): `#f59e0b` (amber-500)

### Border Colors (Left Border - 4px)
- Positive dominant (>40%): `border-l-emerald-500`
- Negative dominant (>40%): `border-l-red-500`
- Mixed/Neutral: `border-l-amber-500`

## Component Breakdown

### 1. Page Header
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Hot Topics                                                   ┃
┃  Trending developer tools ranked by engagement and sentiment ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```
- Text: 4xl font, bold
- Gradient: emerald-400 to blue-500
- Subtitle: gray-400, text-lg

### 2. Time Range Filter
```
┌──────────────────────────────────────────────────────────────┐
│  [Last 24 Hours]  [Last 7 Days ●]  [Last 30 Days]            │
│                              Generated: 5:30 PM • Updating... │
└──────────────────────────────────────────────────────────────┘
```
- Active button: emerald-600 background, white text, shadow
- Inactive button: glass-card, gray-300 text
- Last updated: gray-400, text-sm
- Updating indicator: emerald-400, animate-pulse

### 3. Hot Topic Card
```
┌────────────────────────────────────────────────────────────────┐
│  #1  GitHub Copilot                        ║ EMERALD BORDER   │
│                                             ║                  │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐│
│  │ Engagement   │ Mentions     │ Comments     │ Upvotes      ││
│  │ Score        │              │              │              ││
│  │ 1,250        │ 25           │ 480          │ 310          ││
│  └──────────────┴──────────────┴──────────────┴──────────────┘│
│                                                                │
│  Sentiment Distribution                                        │
│  🟢 72.0% (18)   🔴 16.0% (4)   ⚪ 12.0% (3)                   │
│  [████████████████──────]                                      │
└────────────────────────────────────────────────────────────────┘
```

**Card Structure**:
- Container: `glass-card border-l-4 p-6 rounded-lg shadow-md`
- Rank: text-3xl, bold, gray-400
- Tool Name: text-2xl, bold, white
- Metrics Grid: 2x4 on mobile, 4 columns on desktop
- Sentiment bar: h-2, rounded-full, overflow-hidden

**Metrics Display**:
- Label: text-sm, gray-400
- Value: text-2xl (score) or text-xl (others), font-bold
- Engagement Score: emerald-400
- Others: gray-200

**Sentiment Distribution**:
- Dot indicators: w-3 h-3 rounded-full
- Percentages: Font-semibold, colored (emerald/red/gray)
- Counts: text-gray-500, text-sm in parentheses
- Bar chart: Flex container with colored divs, percentage widths

### 4. Loading Skeleton
```
┌────────────────────────────────────────────────────────────────┐
│  [████████████]  [████████████████]          ║ GRAY BORDER   │
│                                             ║                  │
│  [████████]  [████████]  [████████]  [████████]                │
│  [████████]  [████████]  [████████]  [████████]                │
└────────────────────────────────────────────────────────────────┘
```
- Container: glass-card, border-l-gray-600
- Elements: bg-gray-700, rounded, animate-pulse
- 5 skeleton cards displayed during initial load

### 5. Empty State
```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│                     No hot topics found                        │
│                                                                │
│        No trending tools in the last 7 days.                  │
│              Check back later.                                 │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```
- Container: glass-card, p-12, text-center
- Heading: gray-400, text-xl
- Message: gray-500

### 6. Error State
```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│               Failed to load hot topics                        │
│                                                                │
│            Error: Network timeout                              │
│                                                                │
│                    [ Retry ]                                   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```
- Container: glass-card, p-8, text-center
- Heading: red-400, text-xl
- Error message: gray-400
- Retry button: emerald-600, hover:emerald-700

## Responsive Design

### Mobile (< 768px)
- Metrics grid: 2 columns
- Cards: Full width
- Filter buttons: Stack vertically
- Font sizes: Slightly smaller

### Tablet (768px - 1024px)
- Metrics grid: 4 columns
- Cards: Full width with more padding
- Filter buttons: Horizontal

### Desktop (> 1024px)
- Metrics grid: 4 columns
- Cards: Max width container (mx-auto)
- Wider spacing between elements
- Larger text sizes

## Interactions

### Hover Effects
- **HotTopicCard**: `hover:scale-[1.02] transition-transform cursor-pointer`
- **Filter Buttons**: `hover:bg-white/10` (inactive)
- **Retry Button**: `hover:bg-emerald-700`

### Click Handlers
- HotTopicCard: Prepared for navigation to related posts (US2)
- Filter buttons: Updates timeRange state → React Query refetches
- Retry button: Reloads page

### Loading States
- **Initial Load**: Shows 5 skeleton cards
- **Filter Change**: Overlay with "Loading..." message
- **Refetch**: Shows "• Updating..." next to timestamp
- **Error**: Shows error message with retry button

## Accessibility

### Screen Readers
- Semantic HTML (article tags for cards)
- ARIA labels on buttons
- Alt text for sentiment indicators
- Clear focus indicators

### Keyboard Navigation
- Tab through filter buttons
- Tab through hot topic cards
- Enter to activate buttons
- Escape to close modals (future)

### Color Contrast
- WCAG 2.1 AA compliant
- Text contrast: 4.5:1 minimum
- Focus rings: Visible on all interactive elements

## Example Data Scenarios

### Scenario 1: Positive Tool (GitHub Copilot)
- Engagement Score: 1,250
- Mentions: 25 | Comments: 480 | Upvotes: 310
- Sentiment: 72% positive (emerald), 16% negative (red), 12% neutral
- Border: Emerald (positive dominant)

### Scenario 2: Controversial Tool (Cursor)
- Engagement Score: 820
- Mentions: 15 | Comments: 280 | Upvotes: 150
- Sentiment: 48% positive, 44% negative, 8% neutral
- Border: Amber (mixed sentiment)

### Scenario 3: New Tool (Windsurf)
- Engagement Score: 180
- Mentions: 8 | Comments: 45 | Upvotes: 50
- Sentiment: 62% positive, 25% negative, 13% neutral
- Border: Emerald (positive dominant)

### Scenario 4: Below Threshold (Tool X)
- Mentions: 2 (< 3 minimum)
- **Not displayed** (filtered out by backend)

## Performance Targets

- **Initial Load**: < 5 seconds
- **Filter Change**: < 2 seconds
- **Refetch**: < 3 seconds (background)
- **Skeleton Display**: < 100ms
- **Animation Duration**: 200-300ms

## Future Enhancements (US2+)

1. **Click to View Details**:
   - Modal or new page with related posts
   - Post previews with Reddit links
   - Pagination with "Load More"

2. **Advanced Filtering**:
   - Sentiment filter (positive/negative/neutral only)
   - Minimum engagement threshold slider
   - Tool category filter

3. **Sorting Options**:
   - By engagement (default)
   - By mentions
   - By sentiment (most positive/negative)
   - By recency

4. **Visualizations**:
   - Trend charts (engagement over time)
   - Sentiment timeline
   - Tool comparison graphs

5. **User Preferences**:
   - Save favorite time range
   - Bookmark tools
   - Custom alert thresholds
