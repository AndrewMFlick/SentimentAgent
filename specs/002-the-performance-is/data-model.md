# Data Model: Asynchronous Data Collection

**Feature**: 002-the-performance-is  
**Date**: October 14, 2025

## Overview

This feature does not introduce new data entities. It modifies the execution model of existing data collection processes to run asynchronously without changing data structures or persistence logic.

## Existing Entities (No Changes)

### RedditPost

**Purpose**: Represents a Reddit post collected from monitored subreddits

**Attributes**:

- `id` (string): Reddit post identifier
- `title` (string): Post title
- `content` (string): Post body/selftext
- `author` (string): Reddit username
- `subreddit` (string): Source subreddit
- `url` (string): Post URL
- `created_utc` (datetime): Post creation timestamp
- `score` (int): Reddit score/upvotes

**Relationships**:

- Has many Comments (one-to-many)
- Has one SentimentScore (one-to-one)

**No changes required** - Collection mechanism changes but data structure remains identical

### RedditComment

**Purpose**: Represents a comment on a Reddit post

**Attributes**:

- `id` (string): Reddit comment identifier
- `content` (string): Comment text
- `author` (string): Reddit username
- `post_id` (string): Parent post identifier
- `parent_id` (string): Parent comment identifier (if reply)
- `created_utc` (datetime): Comment creation timestamp
- `score` (int): Comment score

**Relationships**:

- Belongs to RedditPost (many-to-one via post_id)
- Has one SentimentScore (one-to-one)

**No changes required** - Async execution doesn't affect data schema

### SentimentScore

**Purpose**: Stores sentiment analysis results for posts and comments

**Attributes**:

- `id` (string): Unique identifier
- `content_id` (string): Reference to post or comment ID
- `content_type` (string): "post" or "comment"
- `subreddit` (string): Source subreddit
- `sentiment` (string): "positive", "negative", or "neutral"
- `score` (float): Sentiment score (-1.0 to 1.0)
- `analyzed_at` (datetime): Analysis timestamp

**Relationships**:

- Belongs to either RedditPost or RedditComment (polymorphic via content_id/content_type)

**No changes required** - Sentiment analysis runs in same thread pool, results saved identically

### DataCollectionCycle

**Purpose**: Tracks collection cycle metadata and progress

**Attributes**:

- `id` (string): Cycle identifier (e.g., "cycle_20251014_093000")
- `start_time` (datetime): Cycle start timestamp
- `end_time` (datetime): Cycle completion timestamp
- `status` (string): "running", "completed", "failed"
- `posts_collected` (int): Count of posts gathered
- `comments_collected` (int): Count of comments gathered
- `subreddits_processed` (list[string]): List of processed subreddits
- `errors` (list[string]): Error messages if any

**State Transitions**:

1. Created → status="running"
2. Collection completes → status="completed", end_time set
3. Collection fails → status="failed", end_time set, errors populated

**No changes required** - Cycle tracking logic runs in thread pool, state updates preserved

## Execution Model Changes (Non-Data)

### AsyncCollectionWrapper (New Code Pattern, Not Data)

**Purpose**: Bridge between async scheduler and synchronous collection

**Execution Flow**:

1. Async scheduler triggers collection
2. Async wrapper acquires event loop
3. Synchronous collection executes in ThreadPoolExecutor
4. Wrapper awaits completion
5. Control returns to event loop

**Not a data entity** - This is an execution pattern, no persistence required

## Validation Rules (Unchanged)

All existing validation rules are preserved:

- Post/comment IDs must be unique
- Sentiment scores must be in range [-1.0, 1.0]
- Timestamps must be UTC
- Subreddit names must match configured list
- Collection cycles must have unique IDs

## Data Integrity Guarantees

**Maintained by async implementation**:

- All posts collected in sync thread → no partial saves
- Comments collected per post → parent-child relationship preserved
- Sentiment analysis sequential → no race conditions
- Database operations use existing sanitization → Unicode handling intact
- Single-worker thread pool → no concurrent write conflicts

## Summary

**No schema changes required**. The feature modifies execution model (sync → async wrapper) but preserves all data structures, relationships, and persistence logic. Existing CosmosDB containers, validation, and sanitization remain unchanged.
