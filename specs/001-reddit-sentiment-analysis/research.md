# Research & Technology Decisions: Reddit Sentiment Analysis

**Feature**: 001-reddit-sentiment-analysis  
**Date**: 2025-10-13  
**Phase**: Phase 0 - Research & Architecture  
**Status**: Complete

## Overview

This document consolidates research findings and technology decisions for the Reddit Sentiment Analysis platform. All decisions are made to support local development with Azure deployment capability.

## Technology Stack Decisions

### 1. Frontend Framework: React with TypeScript

**Decision**: Use React 18+ with TypeScript 5.0+

**Rationale**:
- **Strong ecosystem**: Extensive charting libraries (Chart.js, Recharts, D3.js) for sentiment visualization
- **TypeScript support**: Excellent type safety for API contracts and data models
- **Component reusability**: Dashboard, trending, and agent pages share common components
- **Performance**: Virtual DOM and React 18 concurrent features handle real-time updates efficiently
- **Azure compatibility**: Works seamlessly with Azure Static Web Apps and Container Apps
- **Team familiarity**: React has largest developer community and extensive documentation

**Alternatives Considered**:
- **Vue.js 3**: Excellent choice, slightly smaller ecosystem for data visualization. Would work equally well if team prefers composition API
- **Angular**: Too heavy for this use case, steeper learning curve
- **Svelte**: Great performance but smaller ecosystem and less Azure-specific tooling

**Implementation Notes**:
- Use Vite for fast development and optimized production builds
- Implement React Query for API state management and caching
- Use Chart.js for time-series sentiment charts (simpler than D3.js for standard charts)

---

### 2. Backend Framework: FastAPI (Python)

**Decision**: Use FastAPI with Python 3.11+

**Rationale**:
- **Async support**: Native async/await for handling concurrent Reddit API requests
- **Type safety**: Pydantic models provide runtime validation and OpenAPI generation
- **Performance**: Comparable to Node.js, handles 10,000 posts/day easily
- **ML ecosystem**: Direct access to transformers library for DistilBERT
- **Azure SDK**: Official Azure SDK for Python with CosmosDB support
- **API documentation**: Auto-generated OpenAPI/Swagger docs
- **Reddit integration**: PRAW library is Python-native and well-maintained

**Alternatives Considered**:
- **Flask**: Lacks async support and modern type safety
- **Django**: Too heavy, includes unnecessary ORM and admin features
- **Node.js/Express**: Would require separate Python environment for ML models

**Implementation Notes**:
- Use uvicorn as ASGI server with multiple workers
- Implement dependency injection for testability
- Use APScheduler for 30-minute collection cycles

---

### 3. Database: Azure CosmosDB (NoSQL)

**Decision**: Use Azure CosmosDB with SQL API

**Rationale**:
- **Time-series optimization**: Partition by date for efficient time-range queries
- **Flexible schema**: NoSQL handles evolving Reddit post structures
- **Azure native**: First-class Azure integration with low latency
- **Local development**: CosmosDB emulator for offline development
- **Scalability**: Auto-scales to handle 900k posts + 4.5M comments (90 days)
- **TTL support**: Automatic 90-day data expiration without custom cleanup jobs
- **Global distribution**: Future-proof for multi-region deployment

**Alternatives Considered**:
- **PostgreSQL**: Relational model less optimal for nested comment threads and varying post structures
- **MongoDB**: Similar capabilities but less Azure-native tooling
- **Azure Table Storage**: Too basic, lacks complex querying needed for trending analysis

**Schema Design Decisions**:
- **Partition Key**: `subreddit` + `date` for balanced distribution
- **Containers**: Separate containers for posts, comments, sentiment_scores, trending_topics
- **Indexing**: Composite indexes on `timestamp` + `sentiment_score` for dashboard queries

---

### 4. Sentiment Analysis: DistilBERT (Primary) + LLM (Future)

**Decision**: Start with DistilBERT, design for LLM integration

**Model**: `distilbert-base-uncased-finetuned-sst-2-english`

**Rationale**:
- **Cost-effective**: Runs locally without API costs
- **Performance**: Processes posts in batches, fast enough for 30-minute cycles
- **Accuracy**: 85-90% accuracy on sentiment classification (meets SC-007: >75% target)
- **No external dependencies**: Works offline during development
- **Azure AI Foundry path**: Architecture supports switching to Azure OpenAI/GPT for LLM analysis

**Alternatives Considered**:
- **VADER**: Rule-based, fast but only ~75% accuracy on nuanced technical discussions
- **Direct LLM**: Higher accuracy but high cost ($0.50-2.00 per 1k posts), requires API availability
- **RoBERTa**: More accurate but 2x slower and larger model size

**Implementation Strategy**:
1. **Phase 1**: Deploy DistilBERT locally and in Azure Container Apps
2. **Phase 2**: Add Azure AI Foundry integration for LLM-based analysis as feature flag
3. **Hybrid approach**: Use DistilBERT for bulk analysis, LLM for ambiguous cases or trending posts

**Model Deployment**:
- Load model at application startup (one-time 250MB download)
- Batch process posts in groups of 32 for GPU efficiency
- Cache model in memory for duration of application lifetime

---

### 5. Reddit API Integration: PRAW

**Decision**: Use PRAW (Python Reddit API Wrapper)

**Rationale**:
- **Official wrapper**: Maintained by Reddit community, handles auth and rate limiting
- **OAuth support**: 60 requests/minute for authenticated apps (sufficient for 14 subreddits/30 min)
- **Mature library**: Battle-tested with extensive documentation
- **Stream support**: Can monitor new submissions in real-time if needed
- **Error handling**: Built-in retry logic and rate limit detection

**Rate Limit Strategy**:
- **Collection window**: 5 minutes actual collection time in 30-minute window (25-minute buffer)
- **Requests per cycle**: ~140 requests (14 subreddits × 10 requests average)
- **Rate limit**: 60 req/min = 300 requests in 5 minutes (sufficient with 2x buffer)
- **Retry logic**: Exponential backoff on rate limit errors (429 status)

**Implementation Notes**:
```python
reddit = praw.Reddit(
    client_id="config.reddit_client_id",
    client_secret="config.reddit_secret",
    user_agent="SentimentAgent/1.0"
)
```

---

### 6. AI Agent: LLM with RAG Pattern

**Decision**: Use Azure OpenAI GPT-4 with Retrieval-Augmented Generation (RAG)

**Rationale**:
- **Natural language understanding**: Handles complex queries like "Compare sentiment trends"
- **Context window**: GPT-4 (8k-32k tokens) holds sufficient sentiment data for analysis
- **Azure integration**: Azure OpenAI Service provides enterprise SLA and data privacy
- **RAG pattern**: Query-relevant sentiment data from CosmosDB, inject into prompt
- **Cost control**: Only pays for query processing (estimated $0.03-0.10 per query)

**Architecture**:
1. **Query parsing**: Extract intent (comparison, trend analysis, driver identification)
2. **Data retrieval**: Query CosmosDB for relevant sentiment data and trending topics
3. **Context building**: Format data as structured context for LLM
4. **LLM call**: Send query + context to Azure OpenAI
5. **Response formatting**: Parse LLM response, add data source citations

**Prompt Engineering**:
```python
system_prompt = """You are a sentiment analysis expert. Analyze the provided 
sentiment data and answer user questions with specific data points, dates, and 
examples. Always cite your sources."""

user_prompt = f"""
Query: {user_query}

Sentiment Data:
{formatted_sentiment_data}

Trending Topics:
{formatted_trending_data}

Provide analysis with specific metrics and examples.
```

---

### 7. Local Development Environment: Docker Compose

**Decision**: Use Docker Compose for local development

**Services**:
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - COSMOSDB_EMULATOR=true
      - REDDIT_CLIENT_ID=${REDDIT_CLIENT_ID}
    depends_on:
      - cosmosdb
  
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - VITE_API_URL=http://localhost:8000
  
  cosmosdb:
    image: mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator
    ports: ["8081:8081", "10251-10254:10251-10254"]
    environment:
      - AZURE_COSMOS_EMULATOR_PARTITION_COUNT=10
```

**Rationale**:
- **Environment parity**: Matches Azure Container Apps architecture
- **Dependency isolation**: CosmosDB emulator, backend, frontend all containerized
- **Quick setup**: Single `docker-compose up` command
- **Testing**: Can run integration tests against emulator
- **No Azure account needed**: Full development without cloud dependencies

---

### 8. Azure Deployment Architecture

**Decision**: Azure Container Apps + AI Foundry + CosmosDB

**Services**:
1. **Azure Container Apps (ACA)**: Host backend and frontend containers
   - Auto-scaling based on HTTP traffic
   - Built-in ingress and HTTPS
   - Costs only when running (~$50-150/month for moderate traffic)

2. **Azure CosmosDB**: Production database
   - Provisioned throughput: Start with 400 RU/s (~$24/month)
   - Auto-scale to 4000 RU/s during collection peaks
   - 90-day TTL configured for automatic data expiration

3. **Azure AI Foundry**: LLM hosting (future phase)
   - Azure OpenAI Service for GPT-4
   - Pay-per-token pricing (~$30-100/month for 100-500 queries/day)

4. **Azure Monitor**: Application Insights for observability
   - Request tracing, performance metrics, error tracking
   - ~$5-10/month for expected volume

**Estimated Monthly Cost**:
- CosmosDB: $24-50 (with auto-scaling)
- Container Apps: $50-150 (2 containers, auto-scale)
- AI Foundry (future): $30-100 (LLM queries)
- Monitor/Logging: $5-10
- **Total**: ~$109-310/month (without LLM), ~$139-410/month (with LLM)

**Deployment Strategy**:
```bash
# Deploy to Azure Container Apps
az containerapp create \
  --name sentiment-backend \
  --resource-group sentiment-rg \
  --image <acr-name>.azurecr.io/backend:latest \
  --environment sentiment-env \
  --ingress external \
  --target-port 8000
```

---

## Best Practices & Patterns

### API Design
- **RESTful endpoints**: `/api/v1/dashboard`, `/api/v1/trending`, `/api/v1/agent/query`
- **Versioning**: URL path versioning for future API changes
- **Pagination**: Limit trending topics to 20, support offset-based pagination
- **Caching**: Cache dashboard aggregations for 5 minutes (Redis optional future enhancement)

### Error Handling
- **Retry logic**: Exponential backoff for Reddit API (3 retries, 1s, 2s, 4s delays)
- **Circuit breaker**: Stop calling Reddit API after 5 consecutive failures
- **Graceful degradation**: Continue processing other subreddits if one fails
- **User feedback**: Clear error messages in frontend ("Reddit API temporarily unavailable")

### Security
- **API keys**: Store in Azure Key Vault (production) or environment variables (local)
- **CORS**: Whitelist frontend origin only
- **Rate limiting**: Implement API rate limiting to prevent abuse (100 req/min per IP)
- **Input validation**: Validate all user inputs (subreddit names, query lengths)

### Monitoring & Logging
- **Structured logging**: JSON format with request IDs, timestamps, severity levels
- **Metrics**: Track collection cycle duration, sentiment analysis latency, AI agent response time
- **Alerts**: Alert on failed collection cycles, API errors >10% rate, high latency >5s
- **Dashboard**: Grafana or Azure Monitor dashboards for operational metrics

---

## Open Questions & Future Research

### Resolved in this document
- ✅ Frontend framework selection (React)
- ✅ Backend framework selection (FastAPI)
- ✅ Database choice (CosmosDB)
- ✅ Sentiment model selection (DistilBERT)
- ✅ Local development approach (Docker Compose)
- ✅ Azure deployment architecture (Container Apps)

### Future enhancements (out of scope for Phase 1)
- **Caching layer**: Redis for dashboard query caching (if performance requires)
- **Real-time updates**: WebSocket support for live dashboard updates
- **Multi-language**: Extend sentiment analysis to non-English posts
- **Historical import**: Backfill sentiment data before deployment date
- **Advanced visualizations**: Network graphs for topic clustering

---

## Implementation Readiness

**Status**: ✅ All research complete

**Next Phase**: Phase 1 - Data Model & Contracts Design

**Confidence Level**: HIGH - All technology choices validated with:
- Azure documentation and pricing calculators
- Reddit API documentation and rate limit testing
- DistilBERT model evaluation on sample Reddit data
- FastAPI + CosmosDB integration examples
- Docker Compose local development testing

**Risk Assessment**: LOW
- All technologies have proven Azure deployment patterns
- CosmosDB emulator enables full local development
- DistilBERT provides cost-effective baseline (LLM optional enhancement)
- PRAW rate limits well within requirements
