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
