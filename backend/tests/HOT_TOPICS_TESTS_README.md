# Hot Topics Tests Documentation

## Overview

This document describes the test suite for Feature #012: Hot Topics (User Story 1).

Tests are organized into three categories following the tasks.md specification:
- **Unit Tests** (T017): Test business logic in isolation
- **Integration Tests** (T018): Test API endpoints end-to-end
- **Performance Tests** (T019): Validate performance requirements

## Test Files

### `tests/unit/test_hot_topics_service.py`
**Task**: T017  
**Lines**: 440+ lines  
**Purpose**: Unit tests for HotTopicsService business logic

**Test Classes**:
1. `TestCalculateCutoffTimestamp` - Tests time range calculations (ENABLED)
   - ✅ `test_calculate_cutoff_24h` - Validates 24 hour cutoff calculation
   - ✅ `test_calculate_cutoff_7d` - Validates 7 day cutoff calculation
   - ✅ `test_calculate_cutoff_30d` - Validates 30 day cutoff calculation
   - ✅ `test_calculate_cutoff_invalid_range` - Tests error handling

2. `TestCalculateEngagementScore` - Tests engagement scoring formula (PENDING Phase 3)
   - ⏸️ `test_engagement_score_formula` - Validates: (mentions × 10) + (comments × 2) + upvotes
   - ⏸️ `test_engagement_score_zero_activity` - Edge case: zero activity

3. `TestAggregateSentimentDistribution` - Tests sentiment aggregation (PENDING Phase 3)
   - ⏸️ `test_sentiment_distribution_percentages` - Validates percentage calculations
   - ⏸️ `test_sentiment_distribution_single_sentiment` - Edge case: 100% single sentiment
   - ⏸️ `test_sentiment_distribution_rounding` - Tests percentage rounding
   - ⏸️ `test_sentiment_distribution_zero_mentions` - Edge case: no mentions

4. `TestGetHotTopicsParameters` - Tests parameter validation (ENABLED)
   - ✅ `test_get_hot_topics_default_parameters` - Validates defaults (7d, limit=10)
   - ✅ `test_get_hot_topics_custom_parameters` - Tests custom values
   - ✅ `test_get_hot_topics_invalid_limit_too_low` - Validates limit >= 1
   - ✅ `test_get_hot_topics_invalid_limit_too_high` - Validates limit <= 50
   - ✅ `test_get_hot_topics_invalid_time_range` - Tests error handling

5. `TestGetRelatedPostsParameters` - Tests pagination validation (ENABLED)
   - ✅ `test_get_related_posts_default_parameters` - Validates defaults
   - ✅ `test_get_related_posts_custom_pagination` - Tests offset/limit
   - ✅ `test_get_related_posts_invalid_limit_too_low` - Validates limit >= 1
   - ✅ `test_get_related_posts_invalid_limit_too_high` - Validates limit <= 100
   - ✅ `test_get_related_posts_invalid_offset_negative` - Validates offset >= 0

### `tests/integration/test_hot_topics_api.py`
**Task**: T018  
**Lines**: 580+ lines  
**Purpose**: Integration tests for hot topics API endpoints

**Test Classes**:
1. `TestHotTopicsEndpoint` - Tests GET /api/hot-topics (PENDING Phase 3)
   - ⏸️ `test_get_hot_topics_returns_200` - Basic endpoint functionality
   - ⏸️ `test_get_hot_topics_default_parameters` - Default time_range=7d, limit=10
   - ⏸️ `test_get_hot_topics_time_range_24h` - 24 hour filter
   - ⏸️ `test_get_hot_topics_time_range_30d` - 30 day filter
   - ⏸️ `test_get_hot_topics_custom_limit` - Custom limit parameter
   - ⏸️ `test_get_hot_topics_invalid_time_range` - Error handling (400)
   - ⏸️ `test_get_hot_topics_invalid_limit_too_high` - Limit validation (400)
   - ⏸️ `test_get_hot_topics_invalid_limit_too_low` - Limit validation (400)
   - ⏸️ `test_get_hot_topics_engagement_sorting` - Verifies DESC sort by engagement
   - ⏸️ `test_get_hot_topics_minimum_mentions_threshold` - Validates >= 3 mentions
   - ⏸️ `test_get_hot_topics_empty_results` - No results scenario
   - ⏸️ `test_get_hot_topics_server_error` - 500 error handling

2. `TestRelatedPostsEndpoint` - Tests GET /api/hot-topics/{tool_id}/posts (PENDING Phase 4)
   - ⏸️ `test_get_related_posts_returns_200` - Basic endpoint functionality
   - ⏸️ `test_get_related_posts_pagination` - offset/limit parameters
   - ⏸️ `test_get_related_posts_time_range_filter` - Time filtering
   - ⏸️ `test_get_related_posts_tool_not_found` - 404 error handling
   - ⏸️ `test_get_related_posts_reddit_url_format` - URL validation

### `tests/integration/test_hot_topics_performance.py`
**Task**: T019  
**Lines**: 360+ lines  
**Purpose**: Performance tests validating success criteria

**Test Classes**:
1. `TestHotTopicsPerformance` - Performance benchmarks (PENDING Phase 3)
   - ⏸️ `test_hot_topics_response_time_under_5_seconds` - **SC-001**: < 5s response
   - ⏸️ `test_engagement_calculation_for_50_tools_under_5_seconds` - Scale test
   - ⏸️ `test_hot_topics_24h_filter_response_time` - **SC-005**: < 2s filter change
   - ⏸️ `test_hot_topics_30d_filter_response_time` - 30d filter performance
   - ⏸️ `test_slow_query_logging_enabled` - Monitoring (Phase 6)
   - ⏸️ `test_hot_topics_cache_improves_performance` - Cache validation
   - ⏸️ `test_hot_topics_concurrent_requests` - Concurrency test

2. `TestRelatedPostsPerformance` - Related posts performance (PENDING Phase 4)
   - ⏸️ `test_related_posts_first_page_under_2_seconds` - Initial load < 2s
   - ⏸️ `test_related_posts_pagination_under_1_second` - Cached pagination < 1s

## Test Status Legend

- ✅ **ENABLED**: Test is active and can run now
- ⏸️ **PENDING**: Test is written but skipped until feature implemented
- ❌ **SKIPPED**: Test intentionally not implemented (see reasons below)

## Running Tests

### Run All Hot Topics Tests
```bash
cd backend
source venv/bin/activate
pytest tests/unit/test_hot_topics_service.py tests/integration/test_hot_topics_api.py tests/integration/test_hot_topics_performance.py -v
```

### Run Only Enabled Tests
```bash
# Unit tests (parameter validation tests are enabled)
pytest tests/unit/test_hot_topics_service.py::TestCalculateCutoffTimestamp -v
pytest tests/unit/test_hot_topics_service.py::TestGetHotTopicsParameters -v
pytest tests/unit/test_hot_topics_service.py::TestGetRelatedPostsParameters -v
```

### Run Specific Test Class
```bash
pytest tests/unit/test_hot_topics_service.py::TestCalculateCutoffTimestamp -v
```

### Run Specific Test
```bash
pytest tests/unit/test_hot_topics_service.py::TestCalculateCutoffTimestamp::test_calculate_cutoff_24h -v
```

## Enabling Tests After Implementation

Tests are marked with `@pytest.mark.skip` and include a reason like:
```python
@pytest.mark.skip(reason="Method not yet implemented - Phase 3 (T008)")
```

To enable tests after implementing features:

1. **After implementing T008** (calculate_engagement_score):
   ```python
   # Remove @pytest.mark.skip from:
   # - TestCalculateEngagementScore tests
   ```

2. **After implementing T009** (_aggregate_sentiment_distribution):
   ```python
   # Remove @pytest.mark.skip from:
   # - TestAggregateSentimentDistribution tests
   ```

3. **After implementing T010-T012** (get_hot_topics + API endpoint):
   ```python
   # Remove @pytest.mark.skip from:
   # - TestHotTopicsEndpoint tests
   # - TestHotTopicsPerformance tests
   ```

4. **After implementing T021-T023** (get_related_posts + API endpoint):
   ```python
   # Remove @pytest.mark.skip from:
   # - TestRelatedPostsEndpoint tests
   # - TestRelatedPostsPerformance tests
   ```

## Test Design Patterns

### 1. Mocking Strategy
```python
# Mock database containers
sentiment_scores = Mock()
reddit_posts = Mock()
reddit_comments = Mock()
tools = Mock()

service = HotTopicsService(
    sentiment_scores_container=sentiment_scores,
    reddit_posts_container=reddit_posts,
    reddit_comments_container=reddit_comments,
    tools_container=tools,
)
```

### 2. Async Test Pattern
```python
@pytest.mark.asyncio
async def test_async_method(self, hot_topics_service):
    """Test async service method."""
    result = await hot_topics_service.get_hot_topics()
    assert result.time_range == "7d"
```

### 3. API Testing Pattern
```python
def test_endpoint(self, client):
    """Test FastAPI endpoint."""
    response = client.get("/api/hot-topics")
    assert response.status_code == 200
    data = response.json()
    assert "hot_topics" in data
```

### 4. Performance Testing Pattern
```python
import time

def test_performance(self, client):
    """Test response time."""
    start = time.time()
    response = client.get("/api/hot-topics")
    duration_ms = (time.time() - start) * 1000
    
    assert response.status_code == 200
    assert duration_ms < 5000, f"Took {duration_ms}ms"
```

## Success Criteria Validation

Tests validate these requirements from `specs/012-hot-topics-isn/spec.md`:

| ID | Requirement | Test(s) |
|----|-------------|---------|
| SC-001 | Identify top 10 tools in < 5 seconds | `test_hot_topics_response_time_under_5_seconds` |
| SC-005 | Time range filtering in < 2 seconds | `test_hot_topics_24h_filter_response_time`, `test_hot_topics_30d_filter_response_time` |
| SC-007 | Complete workflow in < 30 seconds | Combination of US1 + US2 tests |

## Frontend Tests (T020)

**Status**: ❌ **NOT IMPLEMENTED**

**Reason**: No existing frontend test infrastructure
- No testing libraries in `frontend/package.json`
- Repository guidelines: "If there is not existing test infrastructure, you can skip adding tests"

**To implement later**:
1. Add testing dependencies:
   ```bash
   cd frontend
   npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
   ```

2. Create test files:
   - `frontend/tests/components/HotTopicsPage.test.tsx`
   - `frontend/tests/components/HotTopicCard.test.tsx`
   - `frontend/tests/components/TimeRangeFilter.test.tsx`

## Coverage Goals

- **Unit Tests**: 100% coverage of HotTopicsService methods
- **Integration Tests**: All API endpoints and error scenarios
- **Performance Tests**: All success criteria timing requirements

## Maintenance

When adding new features:
1. Add corresponding tests in appropriate file
2. Follow existing naming conventions (`test_<feature>_<scenario>`)
3. Include docstrings with Task ID, Purpose, Setup, Assertions
4. Mark with `@pytest.mark.skip` if feature not ready
5. Update this README with new test information

## Questions?

See:
- Feature spec: `specs/012-hot-topics-isn/spec.md`
- Task breakdown: `specs/012-hot-topics-isn/tasks.md`
- Repository guidelines: `CONTRIBUTING.md`
