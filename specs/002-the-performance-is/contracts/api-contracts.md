# API Contracts: Asynchronous Data Collection

**Feature**: 002-the-performance-is  
**Date**: October 14, 2025

## Overview

This feature does **NOT change any API contracts**. All existing endpoints maintain identical request/response formats. The only change is performance characteristics (response times during data collection).

## Existing Endpoints (No Changes)

### Health Check

**Endpoint**: `GET /api/v1/health`

**Request**: None

**Response**:

```json
{
  "status": "healthy",
  "timestamp": "2025-10-14T16:24:14.745856"
}
```

**Performance Requirement Change**:

- Before: May hang during data collection (blocking)
- After: Must respond within 1 second, always

### Sentiment Stats

**Endpoint**: `GET /api/v1/sentiment/stats`

**Query Parameters**:

- `subreddit` (optional, string): Filter by subreddit
- `hours` (optional, int): Time window (default: 24)

**Response**:

```json
{
  "subreddit": "all",
  "time_window_hours": 24,
  "statistics": {
    "total": 4942,
    "positive": 2156,
    "negative": 823,
    "neutral": 1963,
    "avg_sentiment": 0.234
  },
  "timestamp": "2025-10-14T16:24:49.578260"
}
```

**Performance Requirement Change**:

- Before: May timeout during collection
- After: Must respond within 3 seconds during collection

### Recent Posts

**Endpoint**: `GET /api/v1/posts/recent`

**Query Parameters**:

- `subreddit` (optional, string): Filter by subreddit
- `hours` (optional, int): Time window (default: 24)
- `limit` (optional, int): Max results (default: 100)

**Response**:

```json
[
  {
    "id": "1o6g3k7",
    "title": "Post title",
    "content": "Post content",
    "author": "username",
    "subreddit": "Cursor",
    "url": "https://reddit.com/r/Cursor/comments/1o6g3k7/",
    "created_utc": "2025-10-14T10:30:00Z",
    "score": 42
  }
]
```

**Performance Requirement Change**:

- Before: May hang during collection
- After: Must respond within 3 seconds during collection

### Trending Topics

**Endpoint**: `GET /api/v1/trending`

**Query Parameters**:

- `limit` (optional, int): Max topics (default: 20)

**Response**:

```json
[
  {
    "topic": "AI coding assistants",
    "mentions": 156,
    "sentiment_avg": 0.45,
    "subreddits": ["Cursor", "ChatGPTCoding", "programming"]
  }
]
```

**Performance Requirement Change**:

- Before: May timeout during collection
- After: Must respond within 3 seconds during collection

### Monitored Subreddits

**Endpoint**: `GET /api/v1/subreddits`

**Request**: None

**Response**:

```json
{
  "subreddits": [
    "Cursor",
    "Bard",
    "GithubCopilot",
    "claude",
    "windsurf"
  ],
  "count": 5
}
```

**Performance Requirement Change**:

- Before: Instant (no change needed)
- After: Instant (maintained)

## New Endpoint (Optional): Manual Collection Trigger

**Endpoint**: `POST /api/v1/admin/collect`

**Request**: None

**Response**:

```json
{
  "status": "triggered",
  "message": "Data collection started",
  "timestamp": "2025-10-14T16:31:57.043227"
}
```

**Purpose**: Allow manual triggering of collection for testing/debugging

**Performance**: Must return immediately (queues collection, doesn't wait)

**Note**: This endpoint was added during implementation and should be documented

## Performance Contract Summary

| Endpoint | Current Behavior | Required Behavior | Change |
|----------|------------------|-------------------|--------|
| GET /health | May hang | <1s always | ✅ Fixed |
| GET /sentiment/stats | May timeout | <3s during collection | ✅ Fixed |
| GET /posts/recent | May hang | <3s during collection | ✅ Fixed |
| GET /trending | May timeout | <3s during collection | ✅ Fixed |
| GET /subreddits | Instant | Instant | ✅ No change |
| POST /admin/collect | N/A (new) | Instant (async trigger) | ✅ New |

## Breaking Changes

**None**. All response formats remain identical. Only performance characteristics improve.

## Backward Compatibility

**100% compatible**. Clients require no changes. Existing frontend code works without modification.

## Testing Contract

### Performance Test Requirements

1. **Load Test During Collection**:
   - Start data collection cycle
   - Make 50 concurrent requests to each endpoint
   - Verify all responses within timeout limits
   - No HTTP 500 or 504 errors

2. **Startup Test**:
   - Restart application
   - Health check must respond within 10 seconds
   - Even with immediate collection scheduled

3. **Sustained Load Test**:
   - Run for full 30-minute collection cycle
   - Continuous API requests (10 req/s)
   - Verify P95 response time <3s
   - Zero timeouts or errors

## Summary

**API surface unchanged**. Feature is a pure performance optimization. All existing integration tests should pass without modification. Only add performance/load tests to validate non-blocking behavior.
