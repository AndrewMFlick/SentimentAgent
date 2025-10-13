# Quickstart Guide: Reddit Sentiment Analysis

**Feature**: 001-reddit-sentiment-analysis  
**Version**: 1.0.0  
**Last Updated**: 2025-10-13

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (v4.0+): [Install Docker](https://www.docker.com/products/docker-desktop)
- **Git**: [Install Git](https://git-scm.com/downloads)
- **Reddit API Credentials**: [Create Reddit App](https://www.reddit.com/prefs/apps)
- **Python 3.11+** (optional, for local development without Docker)
- **Node.js 18+** (optional, for local frontend development)

## Quick Start (Docker Compose)

The fastest way to get started is using Docker Compose, which runs the entire stack locally:

### 1. Clone the Repository

```bash
git clone https://github.com/yourorg/sentiment-agent.git
cd sentiment-agent
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your Reddit API credentials:

```env
# Reddit API Configuration
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=SentimentAgent/1.0 by YourUsername

# CosmosDB Emulator (local development)
COSMOSDB_ENDPOINT=https://localhost:8081
COSMOSDB_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
COSMOSDB_DATABASE=sentiment_db

# Azure OpenAI (for AI agent - optional for initial setup)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Application Configuration
COLLECTION_INTERVAL_MINUTES=30
DATA_RETENTION_DAYS=90
LOG_LEVEL=INFO

# Frontend Configuration
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Start the Application

```bash
docker-compose up -d
```

This will start:
- **Backend API** (FastAPI): http://localhost:8000
- **Frontend** (React/Vite): http://localhost:3000
- **CosmosDB Emulator**: https://localhost:8081

### 4. Initialize the Database

Wait for containers to start (~30 seconds), then initialize the database:

```bash
docker-compose exec backend python scripts/init_db.py
```

This script creates CosmosDB containers and seeds the 14 AI tools.

### 5. Trigger Initial Data Collection

Start the first data collection cycle:

```bash
docker-compose exec backend python scripts/trigger_collection.py
```

Or wait 30 minutes for the automatic collection cycle to run.

### 6. Access the Application

Open your browser and navigate to:

- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **API Redoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## Getting Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in the form:
   - **Name**: SentimentAgent (or your choice)
   - **App type**: Select "script"
   - **Description**: Reddit sentiment analysis tool
   - **About URL**: (optional)
   - **Redirect URI**: http://localhost:8000
4. Click "Create app"
5. Copy your **client ID** (under the app name) and **client secret**
6. Update `.env` file with these credentials

## Monitored Subreddits

The application monitors these 14 subreddits by default:

| AI Tool | Subreddits |
|---------|------------|
| Cursor | r/Cursor |
| Google Bard | r/Bard |
| GitHub Copilot | r/GithubCopilot, r/programming |
| Claude | r/claude |
| Windsurf | r/windsurf |
| ChatGPT | r/ChatGPTCoding, r/OpenAI |
| Vibe Coding | r/vibecoding |
| AWS AI | r/aws |
| General AI/ML | r/MachineLearning, r/artificial |
| Kiro IDE | r/kiroIDE |
| Jules Agent | r/JulesAgent |

## Local Development (Without Docker)

If you prefer to run components locally without Docker:

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database initialization
python scripts/init_db.py

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### CosmosDB Emulator

Download and install the [Azure CosmosDB Emulator](https://learn.microsoft.com/en-us/azure/cosmos-db/local-emulator):

- **Windows**: Download MSI installer
- **macOS/Linux**: Use Docker: `docker run -p 8081:8081 mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator`

## Project Structure

```
sentiment-agent/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # REST API routes
│   │   ├── models/            # Data models (Pydantic)
│   │   ├── services/          # Business logic
│   │   ├── repositories/      # CosmosDB data access
│   │   ├── config/            # Configuration management
│   │   └── main.py            # FastAPI application entry
│   ├── scripts/               # Utility scripts
│   │   ├── init_db.py         # Database initialization
│   │   └── trigger_collection.py  # Manual data collection
│   ├── tests/                 # pytest tests
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React + TypeScript frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client
│   │   ├── types/             # TypeScript type definitions
│   │   └── App.tsx            # React app entry
│   ├── tests/                 # Jest + Testing Library tests
│   └── package.json           # Node dependencies
│
├── docker-compose.yml          # Docker Compose configuration
├── .env.example                # Environment variables template
└── README.md                   # Project documentation
```

## Common Commands

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild containers after code changes
docker-compose up -d --build

# Execute command in backend container
docker-compose exec backend python scripts/init_db.py

# Access backend shell
docker-compose exec backend bash
```

### Backend Commands

```bash
# Run tests
pytest tests/

# Run tests with coverage
pytest --cov=app tests/

# Format code
black app/ tests/
isort app/ tests/

# Lint code
flake8 app/ tests/
mypy app/

# Manual data collection
python scripts/trigger_collection.py

# Database initialization
python scripts/init_db.py
```

### Frontend Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Type check
npm run type-check

# Lint code
npm run lint
```

## Data Collection Cycle

The application collects Reddit data every **30 minutes**:

1. **Data Collection**: Fetches new posts and comments from 14 subreddits
2. **Sentiment Analysis**: Analyzes text using DistilBERT
3. **Trending Detection**: Identifies trending topics by engagement velocity
4. **Dashboard Update**: Updates sentiment metrics and visualizations

You can view collection logs:

```bash
docker-compose logs -f backend | grep "collection_cycle"
```

## Troubleshooting

### CosmosDB Emulator Connection Error

**Error**: `Failed to connect to CosmosDB`

**Solution**:
1. Ensure CosmosDB emulator container is running: `docker-compose ps`
2. Check emulator health: `curl -k https://localhost:8081/_explorer/index.html`
3. Verify `COSMOSDB_ENDPOINT` in `.env` is correct
4. Trust emulator SSL certificate (first time only):
   ```bash
   curl -k https://localhost:8081/_explorer/emulator.pem > /tmp/cosmos.pem
   # Import certificate to system trust store
   ```

### Reddit API Rate Limit

**Error**: `RateLimitError: Rate limit exceeded`

**Solution**:
- Reddit API allows **60 requests per minute** with OAuth
- The application automatically retries with exponential backoff
- If persistent, reduce collection frequency or number of monitored subreddits

### Frontend Not Loading

**Error**: Frontend shows blank page or CORS errors

**Solution**:
1. Check backend is running: `curl http://localhost:8000/api/v1/health`
2. Verify `VITE_API_BASE_URL` in `.env` is `http://localhost:8000`
3. Restart frontend: `docker-compose restart frontend`
4. Clear browser cache and hard reload (Ctrl+Shift+R)

### Sentiment Analysis Slow

**Issue**: Sentiment analysis taking >10 seconds per cycle

**Solution**:
- DistilBERT runs on CPU by default (45ms per item)
- For GPU acceleration, update `docker-compose.yml`:
  ```yaml
  backend:
    runtime: nvidia
    environment:
      - CUDA_VISIBLE_DEVICES=0
  ```
- Requires NVIDIA Docker runtime and GPU

## Next Steps

- **Customize Subreddits**: Edit `backend/app/config/ai_tools.json` to monitor different subreddits
- **Configure Sentiment Engine**: Switch between DistilBERT and LLM in settings UI
- **Deploy to Azure**: Follow deployment guide in `docs/deployment.md`
- **Add Authentication**: Enable API key authentication for production
- **Scale Up**: Increase CosmosDB RU/s for higher traffic

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Example API calls:

```bash
# Get dashboard data
curl http://localhost:8000/api/v1/dashboard?timeRange=7d

# Get trending topics
curl http://localhost:8000/api/v1/trending?limit=20

# Query AI agent
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is driving negative sentiment for Cursor?"}'
```

## Support

For issues and questions:

- **GitHub Issues**: https://github.com/yourorg/sentiment-agent/issues
- **Documentation**: https://github.com/yourorg/sentiment-agent/wiki
- **Discussions**: https://github.com/yourorg/sentiment-agent/discussions

## License

MIT License - see `LICENSE` file for details.
