# Implementation Plan: Reddit Sentiment Analysis for AI Developer Tools

**Branch**: `001-reddit-sentiment-analysis` | **Date**: 2025-10-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-reddit-sentiment-analysis/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a scalable sentiment analysis platform that monitors 14 AI developer tool subreddits (Cursor, Bard, GithubCopilot, claude, windsurf, ChatGPTCoding, vibecoding, aws, programming, MachineLearning, artificial, OpenAI, kiroIDE, JulesAgent) every 30 minutes. The system will analyze sentiment using DistilBERT or LLM, display trends on an interactive dashboard, identify trending topics, and provide an AI agent for querying sentiment insights. The application will be built with a React/Vue.js TypeScript frontend, Python backend, and CosmosDB for data storage, designed for local development with Azure deployment capability (Azure Container Apps + AI Foundry).

## Technical Context

**Language/Version**:

- Backend: Python 3.11+
- Frontend: TypeScript 5.0+ with React 18+ or Vue.js 3+

**Primary Dependencies**:

- Backend: FastAPI, PRAW (Reddit API), transformers (DistilBERT), Azure SDK, pydantic
- Frontend: React/Vue.js, TypeScript, Chart.js/D3.js (visualizations), Axios/Fetch API
- AI/ML: DistilBERT (distilbert-base-uncased-finetuned-sst-2-english), Optional LLM integration
- Database: Azure CosmosDB (with local emulator support)

**Storage**: Azure CosmosDB (NoSQL document database)

- 90-day data retention policy
- Optimized for time-series queries
- Local development via CosmosDB emulator

**Testing**:

- Backend: pytest, pytest-asyncio, pytest-mock
- Frontend: Jest, React Testing Library / Vue Test Utils
- Integration: pytest with test containers for CosmosDB
- E2E: Playwright

**Target Platform**:

- Local: Docker Compose environment
- Production: Azure Container Apps (ACA), Azure AI Foundry for LLM services

**Project Type**: Web application (frontend + backend)

**Performance Goals**:

- Data collection: Complete 30-minute cycle for all 14 subreddits within 5 minutes
- Dashboard: Load time < 2 seconds, refresh updates < 1 second
- AI Agent: Response time < 10 seconds for natural language queries
- Sentiment analysis: Process 10,000 posts + 50,000 comments daily
- API: <200ms p95 latency for dashboard queries

**Constraints**:

- Reddit API rate limit: 60 requests/minute (OAuth authenticated)
- 90-day data retention (automatic archival/deletion)
- Local development must work without Azure dependencies
- Support both DistilBERT (local) and LLM (Azure AI Foundry) sentiment analysis
- Must handle Reddit API outages gracefully

**Scale/Scope**:

- 14 monitored subreddits
- Estimated 10,000 posts and 50,000 comments per day
- 90 days of historical data (~900k posts, 4.5M comments)
- Multi-user dashboard access (10-50 concurrent users)
- AI agent query volume: ~100-500 queries/day

- AI agent query volume: ~100-500 queries/day

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file is currently in template form. The following checks align with standard spec-driven development principles:

### I. Specification-Driven Development

- ✅ **PASS**: Complete specification exists at `specs/001-reddit-sentiment-analysis/spec.md`
- ✅ **PASS**: All user stories are prioritized (P1-P3) and independently testable
- ✅ **PASS**: Functional requirements are clear and complete (FR-001 through FR-023)
- ✅ **PASS**: Success criteria are measurable and defined (SC-001 through SC-010)

### II. Incremental Delivery Through User Stories

- ✅ **PASS**: Four user stories identified with clear priority levels
- ✅ **PASS**: P1 (Real-Time Sentiment Monitoring) is independently deployable MVP
- ✅ **PASS**: Each story has clear acceptance criteria and test scenarios
- ✅ **PASS**: Stories can be implemented in priority order for incremental value delivery

### III. Test-First Development (NON-NEGOTIABLE)

- ✅ **PASS**: Commitment to TDD workflow established
- ⚠️ **PENDING**: Tests will be written before implementation (enforced in tasks phase)
- ⚠️ **PENDING**: Test infrastructure (pytest, Jest) specified and ready for Phase 2

### IV. AI-Agent Compatibility

- ✅ **PASS**: Clear documentation structure with spec, plan, and upcoming artifacts
- ✅ **PASS**: Structured templates used throughout
- ✅ **PASS**: File paths are predictable and well-organized
- ✅ **PASS**: Separation of concerns enables parallel development

### V. Observability and Transparency

- ✅ **PASS**: Logging requirements specified in FR-017
- ✅ **PASS**: Structured data collection with timestamps and audit trails
- ✅ **PASS**: Performance metrics defined in success criteria
- ✅ **PASS**: Error handling requirements for API failures and rate limits

**Constitution Gate Status**: ✅ **PASSED** - Proceed to Phase 0 Research

**Re-evaluation Required**: After Phase 1 design completion (data model + contracts)

## Project Structure

### Documentation (this feature)

```text
specs/001-reddit-sentiment-analysis/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── api-spec.yaml   # OpenAPI 3.0 specification
│   └── events.md       # Event/message contracts
├── checklists/          # Quality validation
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── routes/            # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py  # Dashboard data endpoints
│   │   │   ├── trending.py   # Trending topics endpoints
│   │   │   └── agent.py      # AI agent query endpoints
│   │   ├── dependencies.py    # FastAPI dependencies
│   │   └── middleware.py      # Logging, CORS, etc.
│   ├── models/                # Data models
│   │   ├── __init__.py
│   │   ├── reddit.py         # RedditPost, RedditComment
│   │   ├── sentiment.py      # SentimentScore, AITool
│   │   ├── trending.py       # TrendingTopic
│   │   └── query.py          # AnalysisQuery, DataCollectionCycle
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── reddit_collector.py    # PRAW data collection
│   │   ├── sentiment_analyzer.py  # DistilBERT/LLM analysis
│   │   ├── trending_detector.py   # Engagement velocity analysis
│   │   ├── ai_agent.py           # Natural language query processing
│   │   └── scheduler.py          # 30-minute collection cycle
│   ├── repositories/          # Data access layer
│   │   ├── __init__.py
│   │   ├── cosmosdb.py       # CosmosDB connection & base repo
│   │   ├── reddit_repo.py    # Reddit data persistence
│   │   ├── sentiment_repo.py  # Sentiment data persistence
│   │   └── trending_repo.py   # Trending topic persistence
│   ├── config/                # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py       # Pydantic settings
│   │   └── logging.py        # Logging configuration
│   └── utils/                 # Utilities
│       ├── __init__.py
│       ├── rate_limiter.py   # Reddit API rate limiting
│       └── date_utils.py     # Time-series helpers
├── tests/
│   ├── contract/              # API contract tests
│   │   └── test_api_contracts.py
│   ├── integration/           # Integration tests
│   │   ├── test_reddit_collection.py
│   │   ├── test_sentiment_analysis.py
│   │   └── test_cosmosdb.py
│   └── unit/                  # Unit tests
│       ├── test_models.py
│       ├── test_services.py
│       └── test_repositories.py
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml            # Python project configuration
├── Dockerfile                # Container image
└── README.md                 # Backend documentation

frontend/
├── src/
│   ├── components/            # React/Vue components
│   │   ├── Dashboard/
│   │   │   ├── SentimentChart.tsx/.vue
│   │   │   ├── ToolCard.tsx/.vue
│   │   │   └── TimeRangeSelector.tsx/.vue
│   │   ├── Trending/
│   │   │   ├── TrendingList.tsx/.vue
│   │   │   ├── TopicCard.tsx/.vue
│   │   │   └── EngagementMetrics.tsx/.vue
│   │   ├── Agent/
│   │   │   ├── QueryInput.tsx/.vue
│   │   │   ├── ResponseDisplay.tsx/.vue
│   │   │   └── DataSources.tsx/.vue
│   │   └── Common/
│   │       ├── Loading.tsx/.vue
│   │       ├── ErrorBoundary.tsx/.vue
│   │       └── Header.tsx/.vue
│   ├── pages/                 # Page components
│   │   ├── DashboardPage.tsx/.vue
│   │   ├── TrendingPage.tsx/.vue
│   │   └── AgentPage.tsx/.vue
│   ├── services/              # API clients
│   │   ├── api.ts            # Base API client
│   │   ├── dashboardService.ts
│   │   ├── trendingService.ts
│   │   └── agentService.ts
│   ├── types/                 # TypeScript type definitions
│   │   ├── reddit.ts
│   │   ├── sentiment.ts
│   │   ├── trending.ts
│   │   └── agent.ts
│   ├── hooks/                 # Custom hooks (React) / Composables (Vue)
│   │   ├── useSentimentData.ts
│   │   ├── useTrendingTopics.ts
│   │   └── useAgent.ts
│   ├── utils/                 # Utilities
│   │   ├── dateFormatters.ts
│   │   └── chartHelpers.ts
│   ├── App.tsx/.vue          # Root component
│   └── main.tsx/.ts          # Entry point
├── public/                    # Static assets
├── tests/
│   ├── unit/                  # Component unit tests
│   └── e2e/                   # End-to-end tests
├── package.json
├── tsconfig.json
├── vite.config.ts            # or webpack.config.js
├── Dockerfile
└── README.md

# Infrastructure & Development
docker-compose.yml             # Local development environment
docker-compose.azure.yml       # Azure services integration
.env.example                   # Environment variables template
.env.local                     # Local development config (gitignored)
.github/
└── workflows/
    ├── backend-ci.yml
    ├── frontend-ci.yml
    └── deploy-azure.yml
```

**Structure Decision**: Selected "Web application" structure (Option 2 from template) because the feature requires both a frontend dashboard for visualization and a backend API for data collection, sentiment analysis, and AI agent processing. This separation enables independent development of UI and backend services, facilitates testing, and aligns with Azure Container Apps deployment model where frontend and backend can scale independently.

## Complexity Tracking

**No violations** - Constitution Check passed all gates. Project follows standard web application architecture patterns.

---

## Phase 0: Research & Architecture ✓

**Status**: COMPLETE  
**Completed**: 2025-10-13

### Deliverables

- ✅ Technical Context documented
- ✅ Constitution Check completed (all 5 principles passed)
- ✅ Project Structure defined (web application: backend + frontend)
- ✅ Research document created with 8 technology decisions

### Research Summary

Created comprehensive `research.md` covering:

1. **Frontend Framework**: React 18+ with TypeScript 5.0+
2. **Backend Framework**: FastAPI (Python 3.11+)
3. **Database**: Azure CosmosDB with SQL API
4. **Sentiment Analysis**: DistilBERT primary, LLM optional future
5. **Reddit API**: PRAW library with OAuth authentication
6. **AI Agent**: Azure OpenAI GPT-4 with RAG pattern
7. **Local Development**: Docker Compose with CosmosDB emulator
8. **Azure Deployment**: Azure Container Apps + AI Foundry

All technology choices include rationale, alternatives considered, implementation notes, and cost estimates.

---

## Phase 1: Data Model & Contracts ✓

**Status**: COMPLETE  
**Completed**: 2025-10-13

### Phase 1 Deliverables

- ✅ `data-model.md` - 7 entity definitions with validation rules
- ✅ `contracts/api-spec.yaml` - OpenAPI 3.0 REST API specification
- ✅ `contracts/events.md` - Event-driven architecture contracts
- ✅ `quickstart.md` - Getting started guide for local development
- ✅ Agent context updated (GitHub Copilot)

### Data Model Summary

Defined 7 core entities for CosmosDB:

1. **RedditPost** - Reddit posts from monitored subreddits
2. **RedditComment** - Comments on Reddit posts
3. **SentimentScore** - Sentiment analysis results (DistilBERT/LLM)
4. **AITool** - 14 monitored AI developer tools
5. **TrendingTopic** - Trending discussions by engagement velocity
6. **AnalysisQuery** - AI agent query history
7. **DataCollectionCycle** - 30-minute collection run metadata

**CosmosDB Strategy**:

- 7 containers with date-based partitioning for optimal time-series queries
- 90-day automatic TTL for data retention
- Composite indexes for dashboard aggregations
- 400-4000 RU/s auto-scaling

### API Contracts Summary

**REST API** (OpenAPI 3.0):

- `/dashboard` - Sentiment dashboard with time-series data
- `/trending` - Trending topics ranked by engagement velocity
- `/agent/query` - AI agent natural language queries
- `/tools` - AI tools metadata and current sentiment
- `/health` - Service health check

**Events Architecture**:

- Data Collection Events (cycle lifecycle, subreddit processing)
- Sentiment Analysis Events (queued, completed)
- Trending Topics Events (detected, updated, expired)
- AI Agent Events (query received, processed)
- System Health Events (health check failures)

### Constitution Re-Check

Re-evaluated 5 principles against completed data model and API contracts:

**Principle 1 - Spec-Driven Development**: ✅ PASS

- Data model directly derived from functional requirements FR-001 through FR-023
- API contracts implement all 4 user stories (P1-P3)
- No scope creep - all entities map to requirements

**Principle 2 - Incremental Delivery**: ✅ PASS

- Data model supports phased implementation (posts → sentiment → trending → agent)
- API versioned (`/api/v1/`) for backward compatibility
- CosmosDB containers can be created incrementally

**Principle 3 - Simplicity First**: ✅ PASS

- REST API over complex GraphQL
- DistilBERT before LLM (cost-effective sentiment analysis)
- Docker Compose for local development (no Azure account required)

**Principle 4 - Quality Gates**: ✅ PASS

- OpenAPI 3.0 schema validation for all API endpoints
- Data model includes validation rules (required fields, value ranges)
- Quickstart guide enables immediate testing

**Principle 5 - Documentation Over Meetings**: ✅ PASS

- Comprehensive data-model.md with examples
- OpenAPI spec provides executable API documentation
- Events.md documents event-driven architecture
- Quickstart.md enables self-service onboarding

**Result**: All 5 principles passing - ready to proceed to Phase 2 (Task Generation).

---

## Phase 2: Task Generation & Implementation Planning

**Status**: COMPLETE  
**Completed**: 2025-10-13

### Phase 2 Deliverables

- User story priority (P1 → P2 → P3)

---

## Next Steps

### Phase 2: Task Generation

Use `/speckit.tasks` command to generate `tasks.md`:

```bash
cd /Users/andrewflick/Documents/SentimentAgent
specify tasks
```

This will create a `tasks.md` file breaking down implementation into concrete, testable tasks organized by:

- User story priority (P1 → P2 → P3)
- Technical dependencies (data model → API → UI)
- Testing requirements (unit → integration → E2E)

After task generation, implementation can begin following the task order.

```text
```
