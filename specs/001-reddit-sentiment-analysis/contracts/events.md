# Event & Message Contracts

**Feature**: 001-reddit-sentiment-analysis  
**Date**: 2025-10-13  
**Phase**: Phase 1 - Design

## Overview

This document defines the event-driven architecture for the Reddit Sentiment Analysis platform. The system uses an event-based approach for data collection cycles and internal communication between services.

## Event Types

### 1. Data Collection Events

#### CollectionCycleStarted

Emitted when a 30-minute data collection cycle begins.

```json
{
  "eventType": "CollectionCycleStarted",
  "version": "1.0",
  "timestamp": "2025-10-13T10:30:00Z",
  "eventId": "evt_1697197800_start",
  "data": {
    "cycleId": "cycle_20251013_1030",
    "scheduledStartTime": "2025-10-13T10:30:00Z",
    "actualStartTime": "2025-10-13T10:30:02Z",
    "subredditsToProcess": [
      "Cursor", "Bard", "GithubCopilot", "claude", "windsurf",
      "ChatGPTCoding", "vibecoding", "aws", "programming",
      "MachineLearning", "artificial", "OpenAI", "kiroIDE", "JulesAgent"
    ],
    "totalSubreddits": 14
  }
}
```

#### SubredditProcessingStarted

Emitted when processing begins for a specific subreddit.

```json
{
  "eventType": "SubredditProcessingStarted",
  "version": "1.0",
  "timestamp": "2025-10-13T10:30:05Z",
  "eventId": "evt_1697197805_proc_cursor",
  "data": {
    "cycleId": "cycle_20251013_1030",
    "subreddit": "Cursor",
    "processingIndex": 1,
    "totalSubreddits": 14
  }
}
```

#### SubredditProcessingCompleted

Emitted when processing completes for a subreddit.

```json
{
  "eventType": "SubredditProcessingCompleted",
  "version": "1.0",
  "timestamp": "2025-10-13T10:31:12Z",
  "eventId": "evt_1697197872_comp_cursor",
  "data": {
    "cycleId": "cycle_20251013_1030",
    "subreddit": "Cursor",
    "status": "success",
    "metrics": {
      "postsCollected": 12,
      "commentsCollected": 45,
      "totalItemsProcessed": 57,
      "durationMs": 1200,
      "apiCallsMade": 8,
      "rateLimitHits": 0
    },
    "errors": []
  }
}
```

#### SubredditProcessingFailed

Emitted when subreddit processing encounters an error.

```json
{
  "eventType": "SubredditProcessingFailed",
  "version": "1.0",
  "timestamp": "2025-10-13T10:33:00Z",
  "eventId": "evt_1697197980_fail_bard",
  "data": {
    "cycleId": "cycle_20251013_1030",
    "subreddit": "Bard",
    "status": "failed",
    "error": {
      "type": "RateLimitError",
      "message": "Reddit API rate limit exceeded",
      "code": "RATE_LIMIT_429",
      "retryAfterSeconds": 60
    },
    "metrics": {
      "postsCollected": 5,
      "commentsCollected": 0,
      "durationMs": 980,
      "apiCallsMade": 6,
      "rateLimitHits": 1
    },
    "retryAttempt": 3,
    "willRetry": false
  }
}
```

#### CollectionCycleCompleted

Emitted when entire collection cycle finishes.

```json
{
  "eventType": "CollectionCycleCompleted",
  "version": "1.0",
  "timestamp": "2025-10-13T10:35:00Z",
  "eventId": "evt_1697198100_complete",
  "data": {
    "cycleId": "cycle_20251013_1030",
    "startTime": "2025-10-13T10:30:02Z",
    "endTime": "2025-10-13T10:35:00Z",
    "durationSeconds": 298,
    "status": "completed",
    "summary": {
      "subredditsProcessed": 14,
      "subredditsSuccessful": 13,
      "subredditsFailed": 1,
      "totalPostsCollected": 147,
      "totalCommentsCollected": 683,
      "totalItemsProcessed": 830,
      "totalApiCalls": 142,
      "totalRateLimitHits": 1
    },
    "failedSubreddits": [
      {
        "subreddit": "Bard",
        "error": "Rate limit exceeded",
        "willRetryInNextCycle": true
      }
    ]
  }
}
```

### 2. Sentiment Analysis Events

#### SentimentAnalysisQueued

Emitted when content is queued for sentiment analysis.

```json
{
  "eventType": "SentimentAnalysisQueued",
  "version": "1.0",
  "timestamp": "2025-10-13T10:31:15Z",
  "eventId": "evt_1697197875_queue",
  "data": {
    "cycleId": "cycle_20251013_1030",
    "contentIds": [
      "abc123def",
      "xyz789abc",
      "mno456pqr"
    ],
    "contentTypes": {
      "posts": 1,
      "comments": 2
    },
    "totalQueued": 3,
    "analysisMethod": "distilbert"
  }
}
```

#### SentimentAnalysisCompleted

Emitted when sentiment analysis finishes for a batch.

```json
{
  "eventType": "SentimentAnalysisCompleted",
  "version": "1.0",
  "timestamp": "2025-10-13T10:31:20Z",
  "eventId": "evt_1697197880_analyzed",
  "data": {
    "cycleId": "cycle_20251013_1030",
    "batchId": "batch_1697197875",
    "itemsAnalyzed": 3,
    "analysisMethod": "distilbert",
    "modelVersion": "distilbert-base-uncased-finetuned-sst-2-english",
    "results": {
      "positive": 2,
      "negative": 0,
      "neutral": 1
    },
    "averageConfidence": 0.89,
    "totalDurationMs": 135,
    "averageDurationPerItemMs": 45
  }
}
```

### 3. Trending Topics Events

#### TrendingTopicDetected

Emitted when a new trending topic is identified.

```json
{
  "eventType": "TrendingTopicDetected",
  "version": "1.0",
  "timestamp": "2025-10-13T14:00:00Z",
  "eventId": "evt_1697212800_trend",
  "data": {
    "topicId": "trend_20251013_001",
    "theme": "New AI feature release",
    "keywords": ["inline editing", "AI completion", "performance"],
    "aiTool": "Cursor",
    "primaryPostId": "abc123def",
    "relatedPostIds": ["def456ghi", "ghi789jkl"],
    "engagementVelocityScore": 8.7,
    "sentimentDistribution": {
      "positive": 0.65,
      "negative": 0.20,
      "neutral": 0.15
    },
    "firstDetectedAt": "2025-10-13T12:00:00Z",
    "detectionMethod": "engagement_velocity"
  }
}
```

#### TrendingTopicUpdated

Emitted when trending topic metrics are recalculated.

```json
{
  "eventType": "TrendingTopicUpdated",
  "version": "1.0",
  "timestamp": "2025-10-13T14:30:00Z",
  "eventId": "evt_1697214600_trend_update",
  "data": {
    "topicId": "trend_20251013_001",
    "engagementVelocityScore": 9.2,
    "engagementVelocityChange": 0.5,
    "totalUpvotes": 387,
    "totalComments": 152,
    "sentimentDistribution": {
      "positive": 0.68,
      "negative": 0.18,
      "neutral": 0.14
    },
    "newRelatedPosts": ["jkl012mno"],
    "isStillActive": true
  }
}
```

#### TrendingTopicExpired

Emitted when a trending topic becomes inactive.

```json
{
  "eventType": "TrendingTopicExpired",
  "version": "1.0",
  "timestamp": "2025-10-13T18:00:00Z",
  "eventId": "evt_1697227200_trend_expire",
  "data": {
    "topicId": "trend_20251013_001",
    "theme": "New AI feature release",
    "finalEngagementVelocityScore": 3.2,
    "totalLifetimeHours": 6,
    "finalMetrics": {
      "totalUpvotes": 412,
      "totalComments": 168,
      "peakVelocityScore": 9.5,
      "peakVelocityTimestamp": "2025-10-13T15:00:00Z"
    },
    "reason": "engagement_velocity_below_threshold"
  }
}
```

### 4. AI Agent Events

#### AgentQueryReceived

Emitted when user submits a query to AI agent.

```json
{
  "eventType": "AgentQueryReceived",
  "version": "1.0",
  "timestamp": "2025-10-13T15:30:00Z",
  "eventId": "evt_1697223000_query",
  "data": {
    "queryId": "query_1697223000_abc",
    "queryText": "What is driving negative sentiment for Cursor?",
    "userId": "user_123",
    "mentionedTools": ["Cursor"],
    "queryIntent": "sentiment_driver",
    "contextProvided": {
      "timeRange": "7d"
    }
  }
}
```

#### AgentQueryProcessed

Emitted when AI agent completes processing.

```json
{
  "eventType": "AgentQueryProcessed",
  "version": "1.0",
  "timestamp": "2025-10-13T15:30:04Z",
  "eventId": "evt_1697223004_processed",
  "data": {
    "queryId": "query_1697223000_abc",
    "userId": "user_123",
    "processingTimeMs": 3420,
    "llmModel": "gpt-4",
    "tokenUsage": {
      "promptTokens": 1200,
      "completionTokens": 450,
      "totalTokens": 1650
    },
    "dataSources": [
      {
        "type": "sentiment_score",
        "count": 150,
        "dateRange": {
          "start": "2025-10-06",
          "end": "2025-10-13"
        }
      }
    ],
    "responseLength": 842
  }
}
```

### 5. System Health Events

#### HealthCheckFailed

Emitted when health check detects an issue.

```json
{
  "eventType": "HealthCheckFailed",
  "version": "1.0",
  "timestamp": "2025-10-13T16:00:00Z",
  "eventId": "evt_1697224800_health",
  "data": {
    "component": "cosmosdb",
    "status": "unhealthy",
    "error": {
      "type": "ConnectionError",
      "message": "Failed to connect to CosmosDB",
      "code": "ECONNREFUSED"
    },
    "lastSuccessfulCheck": "2025-10-13T15:55:00Z",
    "consecutiveFailures": 3,
    "alertSent": true
  }
}
```

## Event Bus Architecture (Future Enhancement)

For production deployments, events can be published to Azure Event Grid or Service Bus for:

- **Monitoring & Alerting**: Track collection cycle failures, sentiment anomalies
- **Webhooks**: Notify external systems of trending topics
- **Audit Logging**: Maintain event log for compliance
- **Scalability**: Decouple sentiment analysis from data collection

### Example Integration

```python
# Publishing events (future)
from azure.eventhub import EventHubProducerClient, EventData

async def publish_event(event: dict):
    """Publish event to Azure Event Hub"""
    producer = EventHubProducerClient.from_connection_string(
        conn_str=EVENTHUB_CONNECTION_STRING,
        eventhub_name="sentiment-events"
    )
    
    event_data = EventData(json.dumps(event))
    await producer.send_batch([event_data])
```

## Event Schema Validation

All events follow a common envelope:

```json
{
  "eventType": "string (required)",
  "version": "string (required, semantic version)",
  "timestamp": "string (required, ISO 8601)",
  "eventId": "string (required, unique)",
  "data": {
    "...": "event-specific payload"
  }
}
```

**Validation Rules**:
- `eventType`: Must match one of the defined event types
- `version`: Semantic version (e.g., "1.0", "1.1", "2.0")
- `timestamp`: ISO 8601 format, UTC timezone
- `eventId`: Unique identifier, format `evt_{unix_timestamp}_{type}`
- `data`: Event-specific payload (validated per event type)

## Logging & Observability

Events are logged using structured logging:

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "collection_cycle_started",
    event_type="CollectionCycleStarted",
    cycle_id="cycle_20251013_1030",
    subreddits_to_process=14,
    timestamp="2025-10-13T10:30:00Z"
)
```

## Error Handling

Event processing errors are logged but do not halt execution:

- **Transient errors**: Retry with exponential backoff
- **Permanent errors**: Log and continue with next event
- **Critical errors**: Alert operators, graceful degradation

## Event Retention

- **Development**: Events logged to console, not persisted
- **Production**: Events can be streamed to Azure Monitor or Application Insights
- **Retention**: 30 days for operational events, 90 days for audit events
