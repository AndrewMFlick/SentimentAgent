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
- `GET /api/v1/health` - Health check
- `GET /api/v1/subreddits` - List monitored subreddits

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

The application includes:
- Structured logging for all operations
- Health check endpoint for monitoring
- Error handling with retry logic for Reddit API rate limits

## License

See LICENSE file for details.

## Support

For issues and questions, please open an issue on the GitHub repository.
