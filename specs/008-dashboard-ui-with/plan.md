# Implementation Plan: AI Tools Sentiment Analysis Dashboard

**Branch**: `008-dashboard-ui-with` | **Date**: 2025-10-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-dashboard-ui-with/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a dashboard that displays sentiment analysis results segmented by AI tool (GitHub Copilot, Jules AI, etc.), enabling comparison between tools and tracking sentiment trends over time. The system will automatically detect tool mentions in Reddit posts, calculate sentiment breakdowns (positive/negative/neutral), and provide time-series visualization with configurable time ranges. Key features include hybrid tool management (auto-detection with admin approval) and 90-day rolling data retention with extensibility to longer periods.

## Technical Context

**Language/Version**: Python 3.13.3 (backend), TypeScript/React 18 (frontend)

**Primary Dependencies**:

- Backend: FastAPI 0.109.2, Azure Cosmos SDK 4.5.1, structlog 24.1.0, APScheduler 3.10.4
- Frontend: React 18, TypeScript, Vite, Chart.js or Recharts (for time series visualization)

**Storage**: Azure CosmosDB (PostgreSQL mode emulator on localhost:8081, production on Azure)

**Testing**: pytest 8.0.0 (backend), Vitest/React Testing Library (frontend)

**Target Platform**: Web application (desktop + mobile browsers)

**Project Type**: Web application (backend API + frontend SPA)

**Performance Goals**:

- Dashboard load < 2 seconds
- Time series queries (90 days) < 3 seconds
- Tool comparison view < 5 seconds
- Real-time updates within 10 minutes of data collection

**Constraints**:

- CosmosDB PostgreSQL mode limitations (no complex aggregations, workaround with multiple queries)
- 90-day rolling data retention (configurable)
- Must integrate with existing Reddit collector and sentiment analyzer services

**Scale/Scope**:

- Track 5+ AI tools simultaneously
- Support 90 days of historical data with daily granularity
- Handle 10,000+ sentiment records per tool
- Admin interface for tool approval workflow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Applicable Principles** (Based on project patterns):

✅ **Test-First Development**: All new components will have tests written first

- Backend: pytest for API endpoints, database queries, tool detection logic
- Frontend: Vitest/RTL for dashboard components, comparison views, time series charts

✅ **Integration with Existing Services**: Reuse existing infrastructure

- Leverage current Reddit collector (PRAW-based)
- Use existing sentiment analyzer service
- Extend current CosmosDB schema (add tool tracking tables)

✅ **Performance Requirements**: Must meet SC-001, SC-007 success criteria

- Dashboard load < 2s
- Time series queries < 3s
- Use parallel query execution pattern (established in Feature 005)

✅ **Observability**: Structured logging with execution time tracking

- Follow existing structlog patterns
- Log tool detection events, admin approvals, query performance

⚠️ **Complexity Warning**: Adding 3 new database entities (AI Tool, Tool Mention, Time Period Aggregate)

- Justification: Required for tool-specific sentiment tracking and comparison features
- Simpler alternative rejected: Cannot achieve P1 user story without dedicated tool tracking

✅ **No Breaking Changes**: Additive feature, no modifications to existing data models or APIs

## Project Structure

### Documentation (this feature)

```text
specs/008-dashboard-ui-with/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── openapi.yaml     # API contract for tool sentiment endpoints
│   └── events.md        # Tool detection and approval events
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── __init__.py          # [EXISTING] Base models
│   │   ├── ai_tool.py           # [NEW] AI Tool entity
│   │   ├── tool_mention.py      # [NEW] Tool mention tracking
│   │   └── time_aggregate.py    # [NEW] Time period aggregates
│   ├── services/
│   │   ├── database.py          # [EXTEND] Add tool queries
│   │   ├── tool_detector.py     # [NEW] Tool mention detection
│   │   ├── tool_manager.py      # [NEW] Auto-detection + approval
│   │   └── sentiment_aggregator.py  # [NEW] Time series aggregation
│   ├── api/
│   │   ├── routes.py            # [EXISTING] Main routes
│   │   ├── tools.py             # [NEW] Tool sentiment endpoints
│   │   └── admin.py             # [NEW] Admin approval endpoints
│   └── main.py                  # [EXTEND] Register new routes
└── tests/
    ├── unit/
    │   ├── test_tool_detector.py     # [NEW] Tool detection tests
    │   ├── test_tool_manager.py      # [NEW] Tool management tests
    │   └── test_sentiment_aggregator.py  # [NEW] Aggregation tests
    └── integration/
        ├── test_tool_api.py          # [NEW] Tool API integration
        └── test_tool_comparison.py   # [NEW] Comparison API integration

frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx         # [EXISTING] Main dashboard
│   │   ├── ToolSentimentCard.tsx # [NEW] P1: Tool breakdown display
│   │   ├── ToolComparison.tsx    # [NEW] P2: Side-by-side comparison
│   │   ├── SentimentTimeSeries.tsx  # [NEW] P2: Time series chart
│   │   ├── TimeRangeFilter.tsx   # [NEW] P3: Time period filter
│   │   └── AdminToolApproval.tsx # [NEW] Admin approval interface
│   ├── services/
│   │   ├── api.ts                # [EXTEND] Add tool endpoints
│   │   └── toolApi.ts            # [NEW] Tool-specific API client
│   └── types/
│       └── index.ts              # [EXTEND] Add tool types
└── tests/
    ├── components/
    │   ├── ToolSentimentCard.test.tsx
    │   ├── ToolComparison.test.tsx
    │   └── SentimentTimeSeries.test.tsx
    └── integration/
        └── dashboard.test.tsx
```

**Structure Decision**: This is a web application following the existing backend/frontend separation. New functionality is additive - extends existing services and adds new React components without modifying core infrastructure. Backend adds 3 new services (tool_detector, tool_manager, sentiment_aggregator) and frontend adds 5 new components organized by priority (P1-P3 user stories).

## Complexity Tracking

*Note: No constitution violations requiring justification. The 3 new database entities (AI Tool, Tool Mention, Time Period Aggregate) are essential for the feature requirements and represent appropriate domain complexity, not over-engineering.*
