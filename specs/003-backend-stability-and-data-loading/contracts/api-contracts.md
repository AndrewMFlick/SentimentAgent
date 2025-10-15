# API Contracts: Backend Stability and Data Loading

**Feature**: 003-backend-stability-and-data-loading  
**Phase**: 1 (Design)  
**Date**: January 15, 2025

## Overview

This document specifies API contract changes for the backend stability feature. Only one endpoint is modified: `/health` is enhanced with additional metrics. All other endpoints remain unchanged.

---

## Modified Endpoints

### GET /health (Enhanced)

**Status**: MODIFIED (additional fields, backward compatible)

**Purpose**: Health check endpoint with process and application metrics for monitoring backend stability.

#### Request

```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Query Parameters**: None

**Headers**: None required

#### Response (Success)

**Status Code**: `200 OK`

**Content-Type**: `application/json`

**Body Schema**:

```typescript
interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;  // ISO 8601 UTC timestamp
  process: {
    uptime_seconds: number;      // How long the app has been running
    memory_mb: number;            // Current memory usage in MB
    cpu_percent: number;          // CPU usage percentage (0-100)
  };
  application: {
    last_collection_at: string | null;  // ISO 8601 timestamp of last collection
    collections_succeeded: number;       // Total successful collections since startup
    collections_failed: number;          // Total failed collections since startup
    data_freshness_minutes: number | null; // Minutes since last collection (null if never)
  };
  database: {
    connected: boolean;           // Database connection status
  };
}
```

**Example Response**:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "process": {
    "uptime_seconds": 3600,
    "memory_mb": 256.5,
    "cpu_percent": 2.1
  },
  "application": {
    "last_collection_at": "2025-01-15T10:00:00.000Z",
    "collections_succeeded": 48,
    "collections_failed": 0,
    "data_freshness_minutes": 30
  },
  "database": {
    "connected": true
  }
}
```

#### Response (Degraded)

**Status Code**: `200 OK` (still returns 200, but status field indicates degraded)

**Example**:

```json
{
  "status": "degraded",
  "timestamp": "2025-01-15T11:00:00.000Z",
  "process": {
    "uptime_seconds": 5400,
    "memory_mb": 480.2,
    "cpu_percent": 45.3
  },
  "application": {
    "last_collection_at": "2025-01-15T10:00:00.000Z",
    "collections_succeeded": 48,
    "collections_failed": 3,
    "data_freshness_minutes": 60
  },
  "database": {
    "connected": true
  }
}
```

**Degraded Conditions**:

- `data_freshness_minutes > 45` (data collection is delayed)
- `collections_failed / collections_succeeded > 0.1` (>10% failure rate)
- `memory_mb > 450` (approaching memory limit)

#### Response (Unhealthy)

**Status Code**: `503 Service Unavailable`

**Example**:

```json
{
  "status": "unhealthy",
  "timestamp": "2025-01-15T12:00:00.000Z",
  "process": {
    "uptime_seconds": 8400,
    "memory_mb": 510.0,
    "cpu_percent": 98.5
  },
  "application": {
    "last_collection_at": "2025-01-15T10:00:00.000Z",
    "collections_succeeded": 48,
    "collections_failed": 12,
    "data_freshness_minutes": 120
  },
  "database": {
    "connected": false
  }
}
```

**Unhealthy Conditions** (returns 503):

- `database.connected == false` (critical dependency unavailable)
- `data_freshness_minutes > 120` (no collections for 2+ hours)
- `memory_mb > 500` (near memory limit, may crash)

#### Error Responses

**500 Internal Server Error** (unexpected error):

```json
{
  "detail": "Failed to retrieve health metrics: <error message>"
}
```

---

## Unchanged Endpoints

The following endpoints have **no changes**:

### GET /posts/recent

**Status**: UNCHANGED

Returns recent posts based on `collected_at` timestamp. Behavior remains the same.

### GET /posts/trending

**Status**: UNCHANGED

Returns trending posts. No API changes.

### GET /subreddits

**Status**: UNCHANGED

Returns list of tracked subreddits. No changes.

### GET /sentiment/summary

**Status**: UNCHANGED

Returns sentiment analysis summary. No changes.

---

## Backward Compatibility

### Breaking Changes

**None**. The `/health` endpoint enhancement is **additive only**:

- Old fields: None removed
- New fields: Additional fields added to response
- Status codes: 200 OK still returned for healthy state
- Clients ignoring new fields will continue to work

### Migration Path

No migration required for API consumers. The enhanced `/health` endpoint can be consumed immediately by:

1. **Monitoring tools**: Parse new metrics for alerting
2. **Frontend**: Optionally display health status
3. **Load balancers**: Use `status` field for health checks

**Recommended client update**:

```typescript
// Before (still works)
const health = await fetch('/health');
if (health.ok) {
  console.log('Backend is healthy');
}

// After (enhanced)
const health = await fetch('/health');
const data = await health.json();
if (data.status === 'healthy') {
  console.log(`Backend healthy, uptime: ${data.process.uptime_seconds}s`);
} else if (data.status === 'degraded') {
  console.warn('Backend degraded:', data.application);
}
```

---

## Health Status Decision Logic

```python
def determine_health_status(metrics: dict) -> str:
    """Determine overall health status from metrics"""
    
    # Critical failures → unhealthy (503)
    if not metrics["database"]["connected"]:
        return "unhealthy"
    
    if metrics["application"]["data_freshness_minutes"] and metrics["application"]["data_freshness_minutes"] > 120:
        return "unhealthy"
    
    if metrics["process"]["memory_mb"] > 500:
        return "unhealthy"
    
    # Degraded conditions → degraded (200 but flagged)
    if metrics["application"]["data_freshness_minutes"] and metrics["application"]["data_freshness_minutes"] > 45:
        return "degraded"
    
    total_collections = metrics["application"]["collections_succeeded"] + metrics["application"]["collections_failed"]
    if total_collections > 0:
        failure_rate = metrics["application"]["collections_failed"] / total_collections
        if failure_rate > 0.1:  # >10% failure rate
            return "degraded"
    
    if metrics["process"]["memory_mb"] > 450:
        return "degraded"
    
    # All good
    return "healthy"
```

---

## OpenAPI Specification (Partial)

```yaml
paths:
  /health:
    get:
      summary: Health check endpoint
      description: Returns backend health status with process and application metrics
      operationId: health_check
      responses:
        '200':
          description: Health check successful (may be healthy or degraded)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'
        '503':
          description: Service unhealthy (critical failure)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'

components:
  schemas:
    HealthResponse:
      type: object
      required:
        - status
        - timestamp
        - process
        - application
        - database
      properties:
        status:
          type: string
          enum: [healthy, degraded, unhealthy]
        timestamp:
          type: string
          format: date-time
        process:
          $ref: '#/components/schemas/ProcessMetrics'
        application:
          $ref: '#/components/schemas/ApplicationMetrics'
        database:
          $ref: '#/components/schemas/DatabaseStatus'
    
    ProcessMetrics:
      type: object
      required:
        - uptime_seconds
        - memory_mb
        - cpu_percent
      properties:
        uptime_seconds:
          type: integer
          minimum: 0
        memory_mb:
          type: number
          format: float
        cpu_percent:
          type: number
          format: float
          minimum: 0
          maximum: 100
    
    ApplicationMetrics:
      type: object
      required:
        - last_collection_at
        - collections_succeeded
        - collections_failed
        - data_freshness_minutes
      properties:
        last_collection_at:
          type: string
          format: date-time
          nullable: true
        collections_succeeded:
          type: integer
          minimum: 0
        collections_failed:
          type: integer
          minimum: 0
        data_freshness_minutes:
          type: integer
          nullable: true
    
    DatabaseStatus:
      type: object
      required:
        - connected
      properties:
        connected:
          type: boolean
```

---

## Testing Contracts

### Unit Tests

```python
# tests/unit/test_health_endpoint.py
async def test_health_endpoint_healthy():
    """Test /health returns healthy status when all systems operational"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "process" in data
    assert "application" in data
    assert "database" in data

async def test_health_endpoint_degraded_stale_data():
    """Test /health returns degraded when data is stale"""
    # Simulate stale data (last collection > 45 minutes ago)
    app_state.last_collection_time = datetime.utcnow() - timedelta(minutes=60)
    
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["application"]["data_freshness_minutes"] > 45

async def test_health_endpoint_unhealthy_db_disconnected():
    """Test /health returns 503 when database is disconnected"""
    # Mock database connection failure
    with patch('src.services.database.is_connected', return_value=False):
        response = await client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"]["connected"] == False
```

### Integration Tests

```python
# tests/integration/test_health_monitoring.py
async def test_health_endpoint_real_metrics():
    """Test /health returns real process metrics"""
    response = await client.get("/health")
    data = response.json()
    
    # Verify process metrics are realistic
    assert data["process"]["uptime_seconds"] > 0
    assert data["process"]["memory_mb"] > 0
    assert 0 <= data["process"]["cpu_percent"] <= 100
    
    # Verify application metrics structure
    assert "collections_succeeded" in data["application"]
    assert "collections_failed" in data["application"]
```

---

## Summary

- **Modified Endpoints**: 1 (`/health`)
- **New Endpoints**: 0
- **Deleted Endpoints**: 0
- **Breaking Changes**: 0
- **Backward Compatible**: ✅ Yes

The enhanced `/health` endpoint provides comprehensive monitoring without breaking existing clients.
