# US2 Manual Testing Guide

This document provides step-by-step instructions for manually testing the User Story 2 (Related Posts) implementation.

## Prerequisites

1. Backend server running (`cd backend && ./start.sh`)
2. Frontend server running (`cd frontend && npm run dev`)
3. Database populated with:
   - Active tools in `Tools` container
   - Sentiment scores with `detected_tool_ids` in `sentiment_scores` container
   - Reddit posts in `reddit_posts` container

## Backend Testing

### 1. Test Related Posts API Endpoint

**Endpoint**: `GET /api/hot-topics/{tool_id}/posts`

**Test Case 1: Basic Request**
```bash
curl "http://localhost:8000/api/hot-topics/{tool_id}/posts?time_range=7d&offset=0&limit=20"
```

**Expected Response**:
```json
{
  "posts": [
    {
      "post_id": "abc123",
      "title": "Post title",
      "excerpt": "Post content preview...",
      "author": "username",
      "subreddit": "programming",
      "created_utc": "2024-01-01T00:00:00Z",
      "reddit_url": "https://reddit.com/r/programming/comments/abc123/...",
      "comment_count": 25,
      "upvotes": 150,
      "sentiment": "positive",
      "engagement_score": 175
    }
  ],
  "total": 45,
  "has_more": true,
  "offset": 0,
  "limit": 20
}
```

**Verification**:
- ✅ Posts are sorted by `engagement_score` DESC (highest first)
- ✅ `engagement_score` = `comment_count` + `upvotes`
- ✅ `excerpt` length ≤ 150 characters (+ "..." if truncated)
- ✅ `reddit_url` starts with "https://reddit.com"
- ✅ `has_more` = true when `offset + limit < total`
- ✅ `total` reflects total matching posts (not paginated count)

**Test Case 2: Pagination**
```bash
# First page
curl "http://localhost:8000/api/hot-topics/{tool_id}/posts?offset=0&limit=20"

# Second page
curl "http://localhost:8000/api/hot-topics/{tool_id}/posts?offset=20&limit=20"

# Third page
curl "http://localhost:8000/api/hot-topics/{tool_id}/posts?offset=40&limit=20"
```

**Verification**:
- ✅ Each page returns different posts
- ✅ `has_more` = false on last page
- ✅ Last page may have fewer than `limit` posts

**Test Case 3: Time Range Filtering**
```bash
# Last 24 hours
curl "http://localhost:8000/api/hot-topics/{tool_id}/posts?time_range=24h"

# Last 7 days
curl "http://localhost:8000/api/hot-topics/{tool_id}/posts?time_range=7d"

# Last 30 days
curl "http://localhost:8000/api/hot-topics/{tool_id}/posts?time_range=30d"
```

**Verification**:
- ✅ Post counts differ based on time range
- ✅ Older time ranges return more posts
- ✅ Posts are filtered by `_ts` field in sentiment_scores

**Test Case 4: Empty Results**
```bash
curl "http://localhost:8000/api/hot-topics/nonexistent-tool-id/posts"
```

**Expected Response**:
```json
{
  "posts": [],
  "total": 0,
  "has_more": false,
  "offset": 0,
  "limit": 20
}
```

**Test Case 5: Invalid Parameters**
```bash
# Invalid limit (should return 400)
curl "http://localhost:8000/api/hot-topics/{tool_id}/posts?limit=0"
curl "http://localhost:8000/api/hot-topics/{tool_id}/posts?limit=101"

# Invalid offset (should return 400)
curl "http://localhost:8000/api/hot-topics/{tool_id}/posts?offset=-1"

# Invalid time_range (should return 400)
curl "http://localhost:8000/api/hot-topics/{tool_id}/posts?time_range=1h"
```

**Expected Response**: HTTP 400 Bad Request with error message

## Frontend Testing

### 2. Test Hot Topics Page Navigation

**Steps**:
1. Navigate to `http://localhost:5173/hot-topics`
2. Wait for hot topics to load (5-10 seconds)
3. Verify hot topics list displays

**Expected**:
- ✅ 5-10 hot topic cards displayed
- ✅ Each card shows rank, tool name, engagement metrics
- ✅ Sentiment distribution visible with color coding
- ✅ Cards have hover effect (scale-[1.02])

### 3. Test Related Posts Navigation

**Steps**:
1. Click on any hot topic card
2. Observe page transition

**Expected**:
- ✅ Page switches to Related Posts view
- ✅ Header shows "Related Posts: {Tool Name}"
- ✅ Back button visible at top
- ✅ Time range filter displayed
- ✅ Initial 20 posts load automatically

### 4. Test Related Post Cards

**Verify each post card displays**:
- ✅ Post title (clickable link)
- ✅ Sentiment icon (👍 positive, 👎 negative, ➖ neutral)
- ✅ Post excerpt (max 3 lines with ellipsis)
- ✅ Metadata row:
  - r/{subreddit}
  - u/{author}
  - Timestamp (relative, e.g., "2 days ago")
  - Comment count with 💬 icon
  - Upvotes with ⬆️ icon
- ✅ "View on Reddit" link at bottom with external link icon
- ✅ Glass morphism styling (`glass-card` class)
- ✅ Hover effect (scale-[1.01])

### 5. Test Reddit Deep Links

**Steps**:
1. Click "View on Reddit" or the post title
2. Verify new tab opens
3. Check URL format

**Expected**:
- ✅ New browser tab opens
- ✅ URL starts with `https://reddit.com/r/`
- ✅ Lands on correct Reddit post
- ✅ Post content matches preview

**Test Multiple Posts**:
- Test at least 5 different posts
- Verify all links work correctly
- Check different subreddits

### 6. Test Time Range Filtering

**Steps**:
1. On Related Posts page, note current post count
2. Click "Last 24 Hours" filter
3. Wait for posts to reload
4. Click "Last 7 Days" filter
5. Click "Last 30 Days" filter

**Expected**:
- ✅ Post count updates when filter changes
- ✅ "Showing X of Y posts" count updates
- ✅ Loading indicator shows during fetch
- ✅ Posts list refreshes
- ✅ Pagination resets (offset=0)
- ✅ 24h < 7d < 30d post counts (generally)

### 7. Test "Load More" Pagination

**Steps**:
1. On Related Posts page with >20 posts
2. Scroll to bottom
3. Verify "Load More" button visible
4. Click "Load More" button
5. Wait for next batch to load
6. Repeat until no more posts

**Expected**:
- ✅ "Load More" button only shows when `has_more=true`
- ✅ Button shows loading spinner while fetching
- ✅ Button disabled during loading
- ✅ New posts append below existing posts (no duplicates)
- ✅ "Showing X of Y posts" count updates
- ✅ Button disappears when all posts loaded
- ✅ "You've reached the end of the list" message shows
- ✅ Posts maintain sort order (engagement DESC)

### 8. Test Loading States

**Steps**:
1. Navigate to Related Posts (initial load)
2. Observe loading skeleton
3. Change time range filter
4. Click "Load More"

**Expected**:
- ✅ Initial load shows 3 skeleton cards
- ✅ Skeleton cards have gray backgrounds with pulse animation
- ✅ Filter change shows existing posts (no skeleton)
- ✅ "Load More" shows spinner on button (posts stay visible)

### 9. Test Error States

**Simulate Error** (disconnect backend or use invalid tool ID):
1. Navigate to Related Posts
2. Observe error state

**Expected**:
- ✅ Red error message displayed
- ✅ Error text explains the issue
- ✅ "Retry" button available
- ✅ Clicking "Retry" attempts to reload

### 10. Test Empty State

**Steps**:
1. Select a tool with no recent posts
2. Set time range to "Last 24 Hours"

**Expected**:
- ✅ Message: "No posts found for this tool in the selected time range."
- ✅ Glass card styling
- ✅ Back button still works
- ✅ Time range filter still visible

### 11. Test Back Navigation

**Steps**:
1. From Related Posts page, click "Back to Hot Topics"
2. Verify navigation

**Expected**:
- ✅ Returns to Hot Topics list
- ✅ Hot topics list still displayed (cached)
- ✅ Time range filter state preserved
- ✅ Same hot topics shown (unless auto-refresh triggered)

### 12. Test Responsive Design

**Test on Different Screen Sizes**:
- Desktop (1920x1080)
- Tablet (768x1024)
- Mobile (375x667)

**Expected**:
- ✅ Layout adapts to screen size
- ✅ Cards stack properly on mobile
- ✅ Text remains readable
- ✅ Buttons accessible
- ✅ No horizontal scroll

### 13. Test Accessibility

**Keyboard Navigation**:
- ✅ Tab through interactive elements
- ✅ Enter key activates buttons/links
- ✅ Focus indicators visible

**Screen Reader**:
- ✅ Post titles announced
- ✅ Link destinations clear
- ✅ Button purposes clear

### 14. Test Performance

**Metrics to Check** (Chrome DevTools):
- ✅ Initial page load < 5 seconds
- ✅ Filter change < 2 seconds
- ✅ "Load More" < 1 second
- ✅ No layout shifts during loading
- ✅ Smooth scroll performance

## Acceptance Criteria Verification

### US2 Acceptance Scenarios

**Scenario 1**: Users see related posts
- ✅ Click hot topic → related posts list displays
- ✅ List shows Reddit posts mentioning the tool

**Scenario 2**: Post metadata displayed
- ✅ Post title visible
- ✅ Excerpt/preview text shown
- ✅ Author username displayed
- ✅ Subreddit source shown
- ✅ Timestamp displayed

**Scenario 3**: Deep links work
- ✅ Click post link → Reddit opens in new tab
- ✅ Correct Reddit thread loads

**Scenario 4**: Comment count displayed
- ✅ Comment count shown with icon
- ✅ Count matches Reddit data

**Scenario 5**: Engagement sorting
- ✅ Posts ordered by (comments + upvotes) DESC
- ✅ High engagement posts appear first
- ✅ Consistent across pagination

**Scenario 6**: "Load More" pagination
- ✅ Initial 20 posts load
- ✅ "Load More" button functional
- ✅ Fetches next 20 posts
- ✅ Button disappears when no more posts

## Success Criteria

- ✅ **SC-001**: Users identify trending tools in < 5 seconds
- ✅ **SC-002**: Reddit links open correctly in 100% of cases
- ✅ **SC-003**: Engagement scores reflect discussion volume
- ✅ **SC-004**: Sentiment percentages accurate
- ✅ **SC-005**: Time range filtering < 2 seconds
- ✅ **SC-007**: Workflow completion < 30 seconds
- ✅ **SC-008**: Post previews contain sufficient context (min 100 chars)

## Test Checklist

Use this checklist during testing:

- [ ] Backend API responds correctly
- [ ] Pagination works (offset/limit)
- [ ] Time range filtering works
- [ ] Posts sorted by engagement
- [ ] Empty results handled
- [ ] Invalid parameters rejected
- [ ] Hot Topics page loads
- [ ] Navigation to Related Posts works
- [ ] Related Post cards display correctly
- [ ] Reddit deep links work
- [ ] Time range filter updates posts
- [ ] "Load More" pagination works
- [ ] Loading states display properly
- [ ] Error states handled gracefully
- [ ] Empty state displays correctly
- [ ] Back navigation works
- [ ] Responsive on mobile/tablet
- [ ] Keyboard navigation works
- [ ] Performance meets targets

## Screenshots to Capture

1. Hot Topics page with ranked list
2. Related Posts page (initial load)
3. Individual Related Post card (close-up)
4. "Load More" button clicked
5. Time range filter in action
6. Empty state
7. Error state
8. Mobile view
9. Reddit link opened in new tab
10. Sentiment indicators (positive, negative, neutral examples)
