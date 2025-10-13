# Tasks: Reddit Sentiment Analysis for AI Developer Tools

**Feature**: 001-reddit-sentiment-analysis  
**Input**: Design documents from `/specs/001-reddit-sentiment-analysis/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/  
**Generated**: 2025-10-13

**Tech Stack**:
- Backend: Python 3.11+ with FastAPI
- Frontend: React 18+ / Vue.js 3 with TypeScript 5.0+
- Database: Azure CosmosDB with SQL API
- ML: DistilBERT (distilbert-base-uncased-finetuned-sst-2-english)
- Infrastructure: Docker Compose (local), Azure Container Apps (production)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- File paths follow web app structure: `backend/` and `frontend/` directories

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure needed by all user stories

- [ ] T001 Create project directory structure: `backend/` and `frontend/` directories per plan.md
- [ ] T002 [P] Initialize Python backend: create `backend/pyproject.toml`, `backend/requirements.txt`, setup FastAPI dependencies
- [ ] T003 [P] Initialize frontend: create `frontend/package.json`, setup React/TypeScript or Vue.js 3/TypeScript with Vite
- [ ] T004 [P] Create Docker Compose configuration: `docker-compose.yml` with backend, frontend, and CosmosDB emulator services
- [ ] T005 [P] Setup environment configuration: create `.env.example` with Reddit API, CosmosDB, Azure OpenAI variables
- [ ] T006 [P] Create backend/app/config/settings.py for environment variable management
- [ ] T007 [P] Setup linting and formatting: Black, isort, flake8 for backend; ESLint, Prettier for frontend

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Initialize CosmosDB: create database initialization script `backend/scripts/init_db.py` that creates 7 containers (posts, comments, sentiment_scores, trending_topics, ai_tools, analysis_queries, collection_cycles) with correct partition keys per data-model.md
- [ ] T009 Seed AI tools: create `backend/scripts/seed_ai_tools.py` to populate ai_tools container with 14 monitored tools and their associated subreddits
- [ ] T010 [P] Create base Pydantic models: `backend/app/models/base.py` with common fields (id, timestamp, ttl)
- [ ] T011 [P] Implement CosmosDB repository base class: `backend/app/repositories/base.py` with CRUD operations
- [ ] T012 [P] Setup FastAPI app structure: create `backend/app/main.py` with app initialization, CORS middleware, error handlers
- [ ] T013 [P] Implement health check endpoint: `backend/app/api/health.py` implementing `/health` from api-spec.yaml
- [ ] T014 [P] Create logging configuration: `backend/app/config/logging.py` with structured logging (structlog)
- [ ] T015 [P] Setup frontend API client: `frontend/src/services/api.ts` with base Axios client, error handling, types

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Real-Time Sentiment Monitoring (Priority: P1) 🎯 MVP

**Goal**: Continuously monitor 14 subreddits every 30 minutes, analyze sentiment of posts/comments, and display current sentiment scores with trends on a dashboard

**Independent Test**: Verify system monitors subreddits, analyzes sentiment every 30 minutes, and displays real-time sentiment data on dashboard. This is the MVP - delivers immediate value without other stories.

### Data Layer for User Story 1

- [ ] T016 [P] [US1] Create RedditPost model: `backend/app/models/reddit_post.py` with validation rules from data-model.md
- [ ] T017 [P] [US1] Create RedditComment model: `backend/app/models/reddit_comment.py` with parent_comment_id, depth fields
- [ ] T018 [P] [US1] Create SentimentScore model: `backend/app/models/sentiment_score.py` with sentiment_class, confidence_score, analysis_method
- [ ] T019 [P] [US1] Create AITool model: `backend/app/models/ai_tool.py` with current_sentiment_score, sentiment_trend
- [ ] T020 [P] [US1] Create DataCollectionCycle model: `backend/app/models/collection_cycle.py` with status, metrics, errors
- [ ] T021 [P] [US1] Create RedditPost repository: `backend/app/repositories/reddit_post_repository.py` extending base, partition key: subreddit_date
- [ ] T022 [P] [US1] Create RedditComment repository: `backend/app/repositories/reddit_comment_repository.py`, partition key: post_id_date
- [ ] T023 [P] [US1] Create SentimentScore repository: `backend/app/repositories/sentiment_score_repository.py`, partition key: ai_tool_date
- [ ] T024 [P] [US1] Create AITool repository: `backend/app/repositories/ai_tool_repository.py` with methods to update sentiment scores
- [ ] T025 [P] [US1] Create DataCollectionCycle repository: `backend/app/repositories/collection_cycle_repository.py`

### Reddit Data Collection for User Story 1

- [ ] T026 [US1] Implement Reddit client wrapper: `backend/app/services/reddit_client.py` using PRAW with OAuth authentication, rate limit handling
- [ ] T027 [US1] Implement data collection service: `backend/app/services/collection_service.py` to fetch posts and comments from 14 subreddits
- [ ] T028 [US1] Add rate limit handling: exponential backoff retry logic in collection_service.py for Reddit API 429 errors
- [ ] T029 [US1] Create collection scheduler: `backend/app/services/scheduler_service.py` using APScheduler to trigger collection every 30 minutes
- [ ] T030 [US1] Implement collection cycle tracking: log start/end times, subreddits processed, errors in DataCollectionCycle

### Sentiment Analysis for User Story 1

- [ ] T031 [US1] Implement DistilBERT sentiment analyzer: `backend/app/services/sentiment/distilbert_analyzer.py` using transformers library
- [ ] T032 [US1] Create sentiment analysis service: `backend/app/services/sentiment_service.py` to analyze posts and comments, save SentimentScore entities
- [ ] T033 [US1] Add batch processing: analyze posts/comments in batches of 50 for efficiency in sentiment_service.py
- [ ] T034 [US1] Implement sentiment aggregation: calculate current_sentiment_score for each AITool after analysis

### Dashboard API for User Story 1

- [ ] T035 [US1] Implement dashboard endpoint: `backend/app/api/dashboard.py` implementing GET `/dashboard` from api-spec.yaml
- [ ] T036 [US1] Implement tool dashboard endpoint: `backend/app/api/dashboard.py` implementing GET `/dashboard/tools/{toolName}` with timeRange parameter
- [ ] T037 [US1] Add time-series aggregation: query sentiment_scores by ai_tool_date with hourly/daily grouping in dashboard service
- [ ] T038 [US1] Implement response caching: add 5-minute cache for dashboard endpoints using cachetools
- [ ] T039 [US1] Implement tools list endpoint: `backend/app/api/tools.py` implementing GET `/tools` and GET `/tools/{toolName}` from api-spec.yaml

### Dashboard UI for User Story 1

- [ ] T040 [P] [US1] Create Dashboard page component: `frontend/src/pages/DashboardPage.tsx` (or .vue) as main container
- [ ] T041 [P] [US1] Create SentimentChart component: `frontend/src/components/Dashboard/SentimentChart.tsx` using Chart.js for time-series visualization
- [ ] T042 [P] [US1] Create ToolCard component: `frontend/src/components/Dashboard/ToolCard.tsx` displaying current sentiment, trend arrow, last update
- [ ] T043 [P] [US1] Create TimeRangeSelector component: `frontend/src/components/Dashboard/TimeRangeSelector.tsx` for 1h/6h/24h/7d/30d options
- [ ] T044 [P] [US1] Create dashboard API service: `frontend/src/services/dashboardService.ts` with getDashboard(), getToolDashboard() methods
- [ ] T045 [P] [US1] Create useSentimentData hook: `frontend/src/hooks/useSentimentData.ts` (or composable for Vue) to fetch and manage dashboard data
- [ ] T046 [US1] Implement auto-refresh: poll dashboard API every 5 minutes in DashboardPage
- [ ] T047 [US1] Add loading and error states: Loading spinner, ErrorBoundary component for dashboard

### Integration for User Story 1

- [ ] T048 [US1] Create manual collection trigger script: `backend/scripts/trigger_collection.py` for testing data collection
- [ ] T049 [US1] End-to-end test: Run collection cycle → analyze sentiment → verify dashboard displays updated data
- [ ] T050 [US1] Add collection logging: log collection events per events.md (CollectionCycleStarted, SubredditProcessingCompleted, etc.)

**Checkpoint**: ✅ User Story 1 complete - MVP functional! Users can view real-time sentiment monitoring for 14 AI tools with 30-minute updates

---

## Phase 4: User Story 4 - Sentiment Analysis Engine Configuration (Priority: P2)

**Goal**: Allow administrators to configure sentiment analysis method (VADER or LLM) to optimize for speed/cost vs accuracy/nuance

**Independent Test**: Switch between VADER and LLM via configuration, process same batch of posts, verify both methods produce sentiment scores. Tests operational flexibility independent of dashboard or trending features.

**Note**: Implementing US4 before US2/US3 because it enhances the core sentiment engine before building advanced features on top of it

### VADER Implementation for User Story 4

- [ ] T051 [P] [US4] Implement VADER sentiment analyzer: `backend/app/services/sentiment/vader_analyzer.py` using vaderSentiment library
- [ ] T052 [P] [US4] Create sentiment analyzer factory: `backend/app/services/sentiment/analyzer_factory.py` to select VADER or DistilBERT based on config

### LLM Implementation for User Story 4

- [ ] T053 [US4] Implement Azure OpenAI sentiment analyzer: `backend/app/services/sentiment/llm_analyzer.py` using Azure OpenAI GPT-4 with sentiment classification prompt
- [ ] T054 [US4] Add LLM rate limiting: implement retry logic and circuit breaker for Azure OpenAI API in llm_analyzer.py
- [ ] T055 [US4] Add emotion dimensions: extract joy, anger, sadness, surprise from LLM response into SentimentScore.emotion_dimensions
- [ ] T056 [US4] Update analyzer factory: add LLM option to analyzer_factory.py based on SENTIMENT_ANALYSIS_METHOD env var

### Configuration UI for User Story 4 (Optional)

- [ ] T057 [P] [US4] Create Settings page: `frontend/src/pages/SettingsPage.tsx` for admin configuration
- [ ] T058 [P] [US4] Add sentiment method selector: radio buttons for VADER/DistilBERT/LLM in SettingsPage
- [ ] T059 [US4] Create settings API endpoint: `backend/app/api/settings.py` implementing GET/POST `/settings` to update configuration
- [ ] T060 [US4] Add method indicator: display which analysis method was used in dashboard ToolCard component

### Integration for User Story 4

- [ ] T061 [US4] Test method switching: verify changing SENTIMENT_ANALYSIS_METHOD env var affects next collection cycle
- [ ] T062 [US4] Compare analyzer outputs: run same posts through VADER, DistilBERT, LLM and log results for accuracy comparison
- [ ] T063 [US4] Document method differences: add comparison table to quickstart.md (speed, cost, accuracy trade-offs)

**Checkpoint**: ✅ User Story 4 complete - System supports VADER, DistilBERT, and LLM sentiment analysis with configurable selection

---

## Phase 5: User Story 2 - Trending Topics Discovery (Priority: P2)

**Goal**: Identify and display trending discussions ranked by engagement velocity (upvotes and comments over time) so users understand what's driving sentiment and community engagement

**Independent Test**: Verify system identifies posts with high engagement velocity, groups related discussions, displays top 20 trending topics. Delivers value by surfacing important discussions without manual searching.

### Data Layer for User Story 2

- [ ] T064 [P] [US2] Create TrendingTopic model: `backend/app/models/trending_topic.py` with engagement_velocity_score, sentiment_distribution, keywords
- [ ] T065 [P] [US2] Create TrendingTopic repository: `backend/app/repositories/trending_topic_repository.py`, partition key: date

### Trending Detection for User Story 2

- [ ] T066 [US2] Implement engagement velocity calculator: `backend/app/services/trending/velocity_calculator.py` using formula from data-model.md: (upvotes_per_hour * 0.6) + (comments_per_hour * 0.4) + (upvote_ratio * 2.0)
- [ ] T067 [US2] Implement trending detection service: `backend/app/services/trending_service.py` to identify posts with velocity score > 5.0
- [ ] T068 [US2] Add keyword extraction: use simple TF-IDF or spaCy to extract keywords from trending posts in trending_service.py
- [ ] T069 [US2] Implement theme clustering: group related posts by keyword similarity using cosine similarity in trending_service.py
- [ ] T070 [US2] Add trending detection to collection cycle: run trending_service after sentiment analysis completes

### Trending API for User Story 2

- [ ] T071 [US2] Implement trending topics endpoint: `backend/app/api/trending.py` implementing GET `/trending` with limit, tool, minVelocity params from api-spec.yaml
- [ ] T072 [US2] Implement trending topic detail endpoint: `backend/app/api/trending.py` implementing GET `/trending/{topicId}` with full post details
- [ ] T073 [US2] Add trending topics to dashboard: update `/dashboard` response to include top 5 trending topics

### Trending UI for User Story 2

- [ ] T074 [P] [US2] Create Trending page component: `frontend/src/pages/TrendingPage.tsx` (or .vue) as main container
- [ ] T075 [P] [US2] Create TrendingList component: `frontend/src/components/Trending/TrendingList.tsx` displaying ranked topics
- [ ] T076 [P] [US2] Create TopicCard component: `frontend/src/components/Trending/TopicCard.tsx` showing theme, keywords, velocity score, sentiment pie chart
- [ ] T077 [P] [US2] Create EngagementMetrics component: `frontend/src/components/Trending/EngagementMetrics.tsx` showing upvotes, comments, velocity graph
- [ ] T078 [P] [US2] Create trending API service: `frontend/src/services/trendingService.ts` with getTrendingTopics(), getTopicDetail() methods
- [ ] T079 [P] [US2] Create useTrendingTopics hook: `frontend/src/hooks/useTrendingTopics.ts` (or composable) to fetch and manage trending data
- [ ] T080 [US2] Add topic detail modal: click on TopicCard opens modal with full post content, comments, related discussions
- [ ] T081 [US2] Add filtering: filter by AI tool, minimum velocity score in TrendingPage

### Integration for User Story 2

- [ ] T082 [US2] Test trending detection: manually create posts with high engagement, verify they appear in trending list within one collection cycle
- [ ] T083 [US2] Test theme clustering: create multiple related posts, verify they're grouped under same theme
- [ ] T084 [US2] Add trending update events: emit TrendingTopicDetected, TrendingTopicUpdated events per events.md

**Checkpoint**: ✅ User Story 2 complete - Users can discover trending discussions and understand what topics are generating engagement

---

## Phase 6: User Story 3 - Interactive AI Analysis Agent (Priority: P3)

**Goal**: Provide an AI agent that accepts natural language queries about sentiment patterns and returns data-driven insights using Azure OpenAI GPT-4 with RAG

**Independent Test**: Submit natural language queries ("What's driving negative sentiment for Cursor?", "Compare sentiment trends between GitHub Copilot and Claude"), verify agent returns accurate answers with data sources. Delivers intelligent insights beyond raw data display.

### Data Layer for User Story 3

- [ ] T085 [P] [US3] Create AnalysisQuery model: `backend/app/models/analysis_query.py` with query_text, response_text, data_sources, token_usage
- [ ] T086 [P] [US3] Create AnalysisQuery repository: `backend/app/repositories/analysis_query_repository.py`, partition key: query_date

### RAG Implementation for User Story 3

- [ ] T087 [US3] Implement data retrieval service: `backend/app/services/agent/data_retriever.py` to fetch relevant sentiment scores, trending topics based on query
- [ ] T088 [US3] Add query intent classifier: parse user query to identify intent (sentiment_driver, comparison, trend_analysis) in data_retriever.py
- [ ] T089 [US3] Implement context builder: format retrieved data into prompt context in `backend/app/services/agent/context_builder.py`
- [ ] T090 [US3] Create Azure OpenAI client: `backend/app/services/agent/openai_client.py` with GPT-4 chat completion, retry logic
- [ ] T091 [US3] Implement AI agent service: `backend/app/services/agent_service.py` orchestrating data retrieval → context building → LLM query → response formatting
- [ ] T092 [US3] Add response validation: verify LLM response includes data sources, date ranges per FR-015

### Agent API for User Story 3

- [ ] T093 [US3] Implement agent query endpoint: `backend/app/api/agent.py` implementing POST `/agent/query` from api-spec.yaml
- [ ] T094 [US3] Add rate limiting: 10 requests per minute per user using slowapi library in agent.py
- [ ] T095 [US3] Implement query history endpoint: `backend/app/api/agent.py` implementing GET `/agent/history` with userId, limit, offset params
- [ ] T096 [US3] Add query tracking: save all queries and responses to AnalysisQuery for audit and improvement

### Agent UI for User Story 3

- [ ] T097 [P] [US3] Create Agent page component: `frontend/src/pages/AgentPage.tsx` (or .vue) as main container
- [ ] T098 [P] [US3] Create QueryInput component: `frontend/src/components/Agent/QueryInput.tsx` with text area, submit button, example queries
- [ ] T099 [P] [US3] Create ResponseDisplay component: `frontend/src/components/Agent/ResponseDisplay.tsx` with formatted answer, data sources section
- [ ] T100 [P] [US3] Create DataSources component: `frontend/src/components/Agent/DataSources.tsx` showing which data was used (sentiment scores, trending topics, date ranges)
- [ ] T101 [P] [US3] Create agent API service: `frontend/src/services/agentService.ts` with queryAgent(), getQueryHistory() methods
- [ ] T102 [P] [US3] Create useAgent hook: `frontend/src/hooks/useAgent.ts` (or composable) to manage query state, loading, errors
- [ ] T103 [US3] Add query history sidebar: display past queries, click to view previous responses in AgentPage
- [ ] T104 [US3] Add example queries: "What's driving negative sentiment for [tool]?", "Compare [tool1] and [tool2]", "What are people discussing about [topic]?"

### Integration for User Story 3

- [ ] T105 [US3] Test sentiment driver query: ask "What's driving negative sentiment for Cursor?" and verify response references actual posts
- [ ] T106 [US3] Test comparison query: ask "Compare sentiment between GitHub Copilot and Claude" and verify comparative analysis
- [ ] T107 [US3] Test trending topic query: ask "What are people discussing about inline editing?" and verify summary of related posts
- [ ] T108 [US3] Add agent query events: emit AgentQueryReceived, AgentQueryProcessed per events.md

**Checkpoint**: ✅ User Story 3 complete - Users can query AI agent with natural language questions and receive data-driven insights

---

## Phase 7: Polish & Integration

**Purpose**: Cross-cutting concerns, deployment, and final touches

### Testing & Quality

- [ ] T109 [P] Create backend unit tests: `backend/tests/unit/` covering models, services, repositories with pytest
- [ ] T110 [P] Create backend integration tests: `backend/tests/integration/` covering API endpoints, database operations with pytest
- [ ] T111 [P] Create frontend unit tests: `frontend/tests/unit/` covering components with Jest + React Testing Library / Vue Test Utils
- [ ] T112 [P] Create E2E tests: `frontend/tests/e2e/` covering full user workflows with Playwright

### Documentation

- [ ] T113 [P] Update README.md: add project overview, quick start, architecture diagram
- [ ] T114 [P] Create CONTRIBUTING.md: developer guidelines, code style, PR process
- [ ] T115 [P] Add API documentation: ensure OpenAPI spec is served at `/docs` and `/redoc`
- [ ] T116 [P] Create deployment guide: `docs/deployment.md` for Azure Container Apps deployment

### Error Handling & Logging

- [ ] T117 Update error handling: ensure all services use structured logging with correlation IDs
- [ ] T118 Add monitoring: implement health check that verifies database connection, last collection cycle time
- [ ] T119 Add alerting: log critical errors (collection failures, database unavailable) for monitoring setup

### Performance & Optimization

- [ ] T120 [P] Add database indexes: verify composite indexes are created per data-model.md
- [ ] T121 [P] Optimize sentiment analysis: batch processing, parallel execution for multiple posts
- [ ] T122 Add response compression: gzip compression for API responses in FastAPI middleware
- [ ] T123 Optimize frontend: lazy loading for dashboard charts, code splitting for pages

### Security

- [ ] T124 Add API key authentication: implement ApiKeyAuth security scheme from api-spec.yaml for production
- [ ] T125 [P] Add CORS configuration: restrict origins to known frontend domains
- [ ] T126 [P] Add input validation: validate all API inputs against OpenAPI schema
- [ ] T127 Add secrets management: move Reddit API keys, Azure OpenAI keys to Azure Key Vault for production

### Deployment

- [ ] T128 Create Dockerfile for backend: `backend/Dockerfile` with Python 3.11, install dependencies
- [ ] T129 Create Dockerfile for frontend: `frontend/Dockerfile` with Node.js 18, build optimized bundle
- [ ] T130 Create Azure deployment: `docker-compose.azure.yml` for Azure Container Apps, CosmosDB connection
- [ ] T131 Setup CI/CD: `.github/workflows/backend-ci.yml` and `frontend-ci.yml` for automated testing
- [ ] T132 Create deployment workflow: `.github/workflows/deploy-azure.yml` for Azure Container Apps deployment

---

## Implementation Strategy

### MVP Scope (User Story 1 Only)

**Recommended first deliverable**: Complete Phase 1 (Setup), Phase 2 (Foundational), and Phase 3 (User Story 1) to deliver a working sentiment monitoring dashboard. This provides immediate value and validates the core data collection and analysis pipeline.

**MVP Tasks**: T001-T050 (50 tasks)

**Timeline Estimate**: 2-3 weeks with one developer

### Incremental Delivery Order

1. **Week 1-3**: MVP (US1 - Real-Time Sentiment Monitoring)
   - Users can view sentiment dashboard with 30-minute updates
   - Validates Reddit API integration, sentiment analysis, CosmosDB storage

2. **Week 4**: US4 - Sentiment Engine Configuration
   - Adds VADER and LLM options for sentiment analysis
   - Allows cost/accuracy optimization

3. **Week 5-6**: US2 - Trending Topics Discovery
   - Adds trending topics page with engagement velocity ranking
   - Provides deeper insight into community discussions

4. **Week 7-8**: US3 - Interactive AI Analysis Agent
   - Adds natural language query interface
   - Delivers most advanced analytical capability

5. **Week 9-10**: Phase 7 - Polish, testing, deployment
   - Production-ready quality, security, monitoring
   - Azure deployment

### Parallel Execution Opportunities

**Within User Story 1 (MVP)**:
- Data layer tasks (T016-T025) can all run in parallel - different model and repository files
- UI components (T040-T047) can run in parallel - different component files
- Backend API endpoints (T035-T039) can run in parallel after services complete

**Cross-Story Parallelization**:
- After foundational phase complete, User Story 4 (T051-T063) can be developed in parallel with User Story 2 (T064-T084)
- Frontend UI development can happen in parallel with backend API development within each story

---

## Task Dependencies

### Critical Path
```
Setup (T001-T007)
  ↓
Foundational (T008-T015) ← BLOCKING for all user stories
  ↓
[Parallel branches]
  ├─ US1: MVP (T016-T050)
  ├─ US4: Config (T051-T063) - depends on T031, T032
  ├─ US2: Trending (T064-T084) - depends on T016-T034
  └─ US3: Agent (T085-T108) - depends on T023, T064
  ↓
Polish (T109-T132)
```

### User Story Dependencies
- **US1 (MVP)**: No dependencies on other stories - fully independent
- **US4 (Config)**: Depends on US1 sentiment service (T031-T032) to have analyzers to configure
- **US2 (Trending)**: Depends on US1 data collection and sentiment analysis (T016-T034) to have data to analyze
- **US3 (Agent)**: Depends on US1 sentiment data (T023) and US2 trending topics (T064) to have data sources for RAG

### File-Level Dependencies (Sequential Tasks)
- T014 depends on T012 (main.py needs base.py)
- T027 depends on T026 (collection service needs Reddit client)
- T032 depends on T031 (sentiment service needs analyzer)
- T037 depends on T035 (dashboard service needs dashboard endpoint)
- T091 depends on T087-T090 (agent service needs all RAG components)

---

## Task Summary

**Total Tasks**: 132

**Tasks per User Story**:
- Setup: 7 tasks (T001-T007)
- Foundational: 8 tasks (T008-T015)
- US1 - Real-Time Sentiment Monitoring: 35 tasks (T016-T050)
- US4 - Sentiment Engine Configuration: 13 tasks (T051-T063)
- US2 - Trending Topics Discovery: 21 tasks (T064-T084)
- US3 - Interactive AI Analysis Agent: 24 tasks (T085-T108)
- Polish & Integration: 24 tasks (T109-T132)

**Parallel Opportunities**: 47 tasks marked [P] can run in parallel (36% of total)

**Independent Test Criteria**:
- ✅ US1: Verify sentiment dashboard displays real-time data from 14 subreddits with 30-minute updates
- ✅ US4: Verify switching analysis methods (VADER/DistilBERT/LLM) produces different sentiment scores
- ✅ US2: Verify trending topics page displays top 20 posts ranked by engagement velocity
- ✅ US3: Verify AI agent answers natural language queries with data-driven insights

**Suggested MVP**: Complete T001-T050 (User Story 1 only) for first deliverable - provides immediate value and validates core architecture.

---

## Notes

- Tests are NOT included as they were not explicitly requested in the feature specification
- All tasks reference exact file paths based on web application structure from plan.md
- Tasks follow TDD-compatible ordering: models → repositories → services → endpoints → UI within each story
- CosmosDB partition keys and TTL values per data-model.md are critical for performance
- Reddit API rate limit (60 requests/min) constrains collection parallelization
- Azure OpenAI costs for LLM sentiment analysis and AI agent should be monitored in production
- Each user story can be independently tested and deployed as an increment
