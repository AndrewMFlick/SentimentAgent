# Reddit Sentiment Analysis App

A scalable sentiment analysis application that monitors AI developer tool discussions on Reddit, providing real-time sentiment analysis, trending topics, and interactive dashboards.

## Features

- **Real-Time Sentiment Monitoring**: Automatically collects and analyzes sentiment from 14 AI developer tool subreddits every 30 minutes
- **Dual Analysis Methods**: Supports both VADER (fast, rule-based) and LLM-based (nuanced) sentiment analysis
- **Interactive Dashboard**: Visualize sentiment trends, distributions, and statistics
- **Hot Topics Page**: Discover trending discussions with high engagement
- **AI Agent**: Query sentiment data with natural language (e.g., "What's driving negative sentiment for Cursor?")
- **Azure Cloud Hosting**: Designed for scalability on Azure infrastructure with multiple deployment options
- **Data Retention**: 90-day historical data for trend analysis

## Monitored Subreddits

- Cursor, Bard, GithubCopilot, Claude, Windsurf
- ChatGPTCoding, Vibecoding, AWS
- Programming, MachineLearning, Artificial, OpenAI
- KiroIDE, JulesAgent

## Architecture

### Backend (Python)
- **Framework**: FastAPI
- **Reddit API**: PRAW library
- **Sentiment Analysis**: VADER + Azure OpenAI (optional)
- **Database**: Azure CosmosDB
- **Scheduler**: APScheduler for automated data collection

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Charts**: Recharts
- **Routing**: React Router

## Prerequisites

- Python 3.11+
- Node.js 18+
- Azure Account with:
  - CosmosDB instance
  - (Optional) Azure OpenAI resource
- Reddit API credentials

## Setup

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run the application
python -m src.main
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 3. Configuration

Edit `backend/.env` with your credentials:

```env
# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret

# Azure CosmosDB
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your_cosmos_key

# Azure OpenAI (Optional)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key
```

## API Endpoints

### Admin Reanalysis Jobs (Feature 013)
Reanalyze historical sentiment data to categorize posts/comments by AI tools. Useful for backfilling tool associations in existing data or recategorizing after tool changes.

- `POST /api/v1/admin/reanalysis/jobs` - Trigger manual reanalysis job
  - **Auth**: Requires `X-Admin-Token` header
  - **Body**: `{"batch_size": 50, "date_range": {"start": "2025-01-01T00:00:00Z", "end": "2025-01-31T23:59:59Z"}, "tool_ids": ["copilot", "claude"]}`
  - All parameters optional - defaults to full dataset reanalysis
  - Returns: `202 Accepted` with job ID and poll URL

- `GET /api/v1/admin/reanalysis/jobs` - List reanalysis jobs
  - **Auth**: Requires `X-Admin-Token` header
  - **Query params**: `?status=queued&limit=20&offset=0`
  - Returns paginated job list with status, progress, statistics

- `GET /api/v1/admin/reanalysis/jobs/{job_id}` - Get job details
  - **Auth**: Requires `X-Admin-Token` header
  - Returns detailed job info including progress, ETA, error log

- `GET /api/v1/admin/reanalysis/jobs/{job_id}/status` - Poll job status
  - **Auth**: Requires `X-Admin-Token` header
  - Returns job status, percentage complete, documents processed, ETA

- `DELETE /api/v1/admin/reanalysis/jobs/{job_id}` - Cancel queued job
  - **Auth**: Requires `X-Admin-Token` header
  - Only queued jobs can be cancelled (not running jobs)

**Example: Trigger Full Reanalysis**
```bash
curl -X POST http://localhost:8000/api/v1/admin/reanalysis/jobs \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your-admin-token" \
  -d '{"batch_size": 100}'
```

**Example: Reanalyze Date Range for Specific Tools**
```bash
curl -X POST http://localhost:8000/api/v1/admin/reanalysis/jobs \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your-admin-token" \
  -d '{
    "batch_size": 50,
    "date_range": {
      "start": "2025-01-01T00:00:00Z",
      "end": "2025-01-31T23:59:59Z"
    },
    "tool_ids": ["copilot", "claude", "cursor"]
  }'
```

**Automatic Reanalysis Triggers**:
- **New Tool Creation**: When a new tool is created with `status='active'`, reanalysis automatically runs to find historical mentions
- **Tool Activation**: Changing a tool from `archived` to `active` triggers reanalysis
- **Tool Merge**: Merging tools (Tool A → Tool B) automatically updates all sentiment records to reference the target tool

**Rate Limiting**: Reanalysis includes built-in rate limiting to prevent overwhelming CosmosDB:
- Configurable delay between batches (default: 100ms)
- Exponential backoff for 429 errors (rate limit exceeded)
- Max retries: 5 attempts with delays up to 60 seconds

**Idempotency**: Reanalysis jobs are safe to run multiple times on the same data. The system updates `detected_tool_ids` based on current detection algorithms.

### Hot Topics
- `GET /api/v1/hot-topics?time_range={24h|7d|30d}` - Get trending tools by engagement score
  - Returns tools sorted by engagement (mentions × avg_score × upvote_ratio)
  - Includes sentiment breakdown, statistics, and top engaged posts
- `GET /api/v1/hot-topics/{tool_id}/posts?time_range={24h|7d|30d}&offset=0&limit=20` - Get related posts for a tool
  - Paginated Reddit posts mentioning the tool, sorted by engagement
  - Supports "Load More" pagination with offset parameter

### Sentiment Analysis
- `GET /api/v1/sentiment/stats` - Get sentiment statistics
- `GET /api/v1/sentiment/trends` - Get sentiment trends over time

### Posts
- `GET /api/v1/posts/recent` - Get recent Reddit posts
- `GET /api/v1/posts/{post_id}` - Get specific post

### Trending
- `GET /api/v1/trending` - Get trending topics

### AI Agent
- `POST /api/v1/ai/query` - Query AI agent with natural language questions

### System
- `GET /api/v1/health` - Comprehensive health check with metrics
- `GET /api/v1/subreddits` - List monitored subreddits

### Health Check Response

The `/api/v1/health` endpoint provides comprehensive backend monitoring:

```json
{
  "status": "healthy",  // or "degraded", "unhealthy"
  "timestamp": "2025-10-15T16:57:33.168Z",
  "process": {
    "uptime_seconds": 3600.5,
    "memory_mb": 245.32,
    "cpu_percent": 2.5,
    "pid": 12345
  },
  "application": {
    "last_collection_at": "2025-10-15T16:45:00.000Z",
    "collections_succeeded": 10,
    "collections_failed": 0,
    "data_freshness_minutes": 12.5
  },
  "database": {
    "connected": true
  }
}
```

**Status Codes**:
- `200`: Healthy (all systems operational)
- `503`: Unhealthy (database disconnected or critical failure)

**Health Status Thresholds**:
- Healthy: Database connected, memory < 512MB
- Degraded: Memory > 512MB or data > 60 minutes old
- Unhealthy: Database disconnected

## Development

### Backend Testing

```bash
cd backend
pytest
```

### Frontend Testing

```bash
cd frontend
npm run lint
npm run build
```

## Deployment

See [deployment/AZURE_DEPLOYMENT.md](deployment/AZURE_DEPLOYMENT.md) for comprehensive deployment guides covering:

- Azure Container Apps (Recommended)
- Azure Kubernetes Service (AKS)
- Azure App Service
- Docker Compose for local deployment

Quick deploy with Docker Compose:

```bash
cd deployment/docker
docker-compose up -d
```

## Project Structure

```
├── backend/
│   ├── src/
│   │   ├── api/          # FastAPI routes
│   │   ├── models/       # Data models
│   │   ├── services/     # Business logic
│   │   ├── config.py     # Configuration
│   │   └── main.py       # Application entry point
│   ├── tests/            # Backend tests
│   └── requirements.txt  # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API client
│   │   ├── types/        # TypeScript types
│   │   └── App.tsx       # Main app component
│   └── package.json      # Node dependencies
│
└── specs/                # Feature specifications
```

## Configuration Options

### Sentiment Analysis Method

Choose between VADER and LLM in `.env`:

```env
SENTIMENT_METHOD=VADER  # or LLM
USE_LLM_FOR_AMBIGUOUS=false  # Use LLM as fallback for low-confidence VADER results
```

### Collection Frequency

Adjust data collection interval:

```env
COLLECTION_INTERVAL_MINUTES=30
```

### Data Retention

Configure how long to keep historical data:

```env
DATA_RETENTION_DAYS=90
```

## Monitoring

The application includes comprehensive health monitoring and stability features:

### Health Monitoring
- **Health Endpoint**: `/api/v1/health` provides real-time metrics
  - Process uptime, memory, and CPU usage
  - Collection success/failure counters
  - Data freshness (time since last collection)
  - Database connection status
- **Status Codes**: Returns 200 (healthy), 503 (unhealthy) for automated monitoring

### Backend Stability Features
- **Graceful Shutdown**: Waits for running jobs to complete before shutdown
- **Error Recovery**: Catch-log-continue pattern for collection errors
- **Database Retry Logic**: Exponential backoff for transient failures
- **Memory Monitoring**: Tracks memory usage per collection cycle
- **Structured Logging**: JSON-formatted logs with full context
- **Data Loading**: Recent data loads on startup (non-blocking)

### External Process Monitor

Monitor backend health from a separate process:

```bash
cd backend
python3 monitoring/process_monitor.py --interval 60
```

**Options**:
- `--api-url`: Backend URL (default: http://localhost:8000)
- `--interval`: Check interval in seconds (default: 60)
- `--quiet`: Only print errors and warnings

## Troubleshooting

### Reanalysis Jobs

**Problem**: Reanalysis job fails with 400 "Cannot start job: X job(s) already active"

**Solution**: Only one reanalysis job can run at a time. Check active jobs:
```bash
curl -H "X-Admin-Token: your-admin-token" \
  http://localhost:8000/api/v1/admin/reanalysis/jobs?status=queued
```

Cancel the active job if needed:
```bash
curl -X DELETE -H "X-Admin-Token: your-admin-token" \
  http://localhost:8000/api/v1/admin/reanalysis/jobs/{job_id}
```

**Problem**: Job stuck in "queued" status

**Solution**: Check backend logs for scheduler errors. The job poller runs every 60 seconds to pick up queued jobs. If the scheduler isn't running, restart the backend.

**Problem**: Job completes but sentiment scores not updated

**Solution**: Check job statistics in the job details:
```bash
curl -H "X-Admin-Token: your-admin-token" \
  http://localhost:8000/api/v1/admin/reanalysis/jobs/{job_id}
```

Look for `errors_count` in statistics. Common issues:
- Documents missing `content` field (skipped)
- Tool detection returning empty results (no matching tools found)
- Database upsert errors (check permissions)

**Problem**: Reanalysis very slow or timing out

**Solution**: Adjust rate limiting in `.env`:
```env
REANALYSIS_BATCH_DELAY_MS=50  # Reduce delay between batches (default: 100)
```

For large datasets (>10k documents), use batch_size parameter:
```json
{"batch_size": 200}  // Larger batches = fewer round trips
```

**Problem**: CosmosDB 429 rate limit errors

**Solution**: The system automatically retries with exponential backoff. If errors persist, reduce batch processing speed in `.env`:
```env
REANALYSIS_BATCH_DELAY_MS=200  # Increase delay between batches
REANALYSIS_MAX_RETRIES=10      # More retry attempts
```

### Admin Panel Access

**Problem**: Admin panel returns 401 Unauthorized

**Solution**: Set admin token in environment:
```env
# backend/.env
ADMIN_TOKEN=your-secret-token-here
```

Use the token in requests:
```bash
curl -H "X-Admin-Token: your-secret-token-here" http://localhost:8000/api/v1/admin/...
```

### Database Connection

**Problem**: "Database connection failed" errors

**Solution**: Verify CosmosDB credentials in `.env`:
- Check `COSMOS_ENDPOINT` matches your Azure CosmosDB account
- Verify `COSMOS_KEY` is correct (primary or secondary key)
- Ensure network connectivity to Azure (firewall rules, VPN)

For CosmosDB emulator (localhost:8081):
```env
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
```

## License

See LICENSE file for details.

## Feature Development Status

### Completed Features ✅

- **[001-reddit-sentiment-analysis](specs/001-reddit-sentiment-analysis/)**: Initial implementation - Merged PR #3
- **[002-the-performance-is](specs/002-the-performance-is/)**: Asynchronous data collection - Merged PR #4
- **[003-backend-stability-and-data-loading](specs/003-backend-stability-and-data-loading/)**: Backend stability improvements - Merged [PR #8](https://github.com/AndrewMFlick/SentimentAgent/pull/8) 
  - See [COMPLETION.md](specs/003-backend-stability-and-data-loading/COMPLETION.md) for full implementation details
- **[004-fix-the-cosmosdb](specs/004-fix-the-cosmosdb/)**: CosmosDB datetime query fix - Merged [PR #16](https://github.com/AndrewMFlick/SentimentAgent/pull/16)

## Support

For issues and questions, please open an issue on the GitHub repository.
