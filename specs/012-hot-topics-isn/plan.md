# Implementation Plan: Enhanced Hot Topics with Tool Insights

**Branch**: `012-hot-topics-isn` | **Date**: 2025-10-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-hot-topics-isn/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

**Primary Requirement**: Display a ranked dashboard of trending developer tools with engagement metrics (mentions, comments, upvotes), sentiment distribution, and related Reddit posts with deep links.

**Technical Approach**: 
- Backend: Calculate engagement scores on-demand from existing sentiment_scores, reddit_posts, and reddit_comments data
- Use existing `detected_tool_ids` field (from feature 004) to identify tool mentions
- Leverage `_ts` field pattern for efficient time-range filtering (from features 004-005)
- Frontend: React Query infinite queries for "Load More" pagination
- No new database tables - all data derived from existing containers via aggregation queries

## Technical Context

**Language/Version**: Python 3.13.3 (backend), TypeScript 5.3.3 (frontend)  
**Primary Dependencies**: 
- Backend: FastAPI 0.109.2, Azure Cosmos SDK 4.5.1, Pydantic 2.10.6, structlog 24.1.0
- Frontend: React 18.2.0, React Query (@tanstack/react-query), TailwindCSS 3.4+, Vite 5.1.0

**Storage**: Azure CosmosDB (SQL API) - existing containers: `reddit_posts`, `reddit_comments`, `sentiment_scores`, `Tools`  
**Testing**: pytest 8.0.0 (backend), Vitest (frontend)  
**Target Platform**: Web application (Linux server backend, modern browsers frontend)  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: 
- Hot topics page load < 5 seconds (SC-001)
- Time range filtering < 2 seconds (SC-005)
- Related posts query < 2 seconds for 20 posts
- Load More pagination < 1 second (server-side cache)

**Constraints**: 
- Must use existing `detected_tool_ids` field (no re-analysis)
- Timeline filtering must exclude posts without engagement in selected range
- Pagination: 20 posts per page with "Load More" button
- Related posts sorted by engagement (comments + upvotes)

**Scale/Scope**: 
- ~50 active tools
- ~10,000 posts with sentiment data
- Top 10 hot topics displayed by default
- Up to 100 related posts per tool (typical case)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ **PASS** - No constitution file exists in repository

**Notes**: 
- No `.specify/memory/constitution.md` file found with project-specific principles
- Default best practices apply: simplicity, testability, maintainability
- This feature follows existing patterns (service layer, FastAPI routes, React components)
- No architectural violations introduced

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── hot_topics.py          # NEW: HotTopic, RelatedPost Pydantic models
│   ├── services/
│   │   └── hot_topics_service.py  # NEW: Engagement calculation, aggregation logic
│   └── api/
│       └── hot_topics.py          # NEW: FastAPI routes for hot topics endpoints
└── tests/
    ├── unit/
    │   └── test_hot_topics_service.py    # NEW: Service unit tests
    └── integration/
        ├── test_hot_topics_api.py        # NEW: API integration tests
        └── test_hot_topics_performance.py # NEW: Performance benchmarks

frontend/
├── src/
│   ├── components/
│   │   ├── HotTopicsPage.tsx       # MODIFIED: Enhanced with engagement metrics
│   │   ├── HotTopicCard.tsx        # NEW: Individual tool card component
│   │   ├── RelatedPostsList.tsx    # NEW: Posts list with Load More
│   │   └── RelatedPostCard.tsx     # NEW: Individual post preview
│   ├── services/
│   │   └── api.ts                  # MODIFIED: Add hot topics API calls
│   └── types/
│       └── hot-topics.ts           # NEW: TypeScript interfaces
└── tests/
    └── components/
        ├── HotTopicsPage.test.tsx
        └── RelatedPostsList.test.tsx
```

**Structure Decision**: Follows existing web application pattern with backend/ and frontend/ directories. Hot topics feature adds new service layer (hot_topics_service.py) following same pattern as sentiment_analyzer.py and trending_analyzer.py. Frontend adds new page component and API integration using existing React Query patterns.

## Complexity Tracking

**No violations** - This feature follows existing architectural patterns and introduces no new complexity:

- Uses existing service layer pattern (similar to sentiment_analyzer.py, trending_analyzer.py)
- Uses existing FastAPI routing pattern (similar to routes.py)
- Uses existing React component patterns (similar to Dashboard.tsx)
- Uses existing database query patterns (`_ts` field filtering from features 004-005)
- No new external dependencies (uses FastAPI, React Query, CosmosDB already in use)
- No new infrastructure components (uses existing backend/frontend deployment)
