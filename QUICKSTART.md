# Quick Start Guide

This guide will help you get the Reddit Sentiment Analysis app running locally in under 10 minutes.

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ installed
- Reddit API credentials ([create app](https://www.reddit.com/prefs/apps))
- Azure CosmosDB instance (or use emulator for development)

## Step 1: Clone and Setup

```bash
git clone <repository-url>
cd SentimentAgent
```

## Step 2: Backend Setup (3 minutes)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

Edit `.env` with your credentials:

```env
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
COSMOS_ENDPOINT=your_cosmos_endpoint
COSMOS_KEY=your_cosmos_key
```

**Using CosmosDB Emulator for Development:**

```env
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
```

Start the backend:

```bash
python -m src.main
```

Backend will be running at <http://localhost:8000>

## Step 3: Frontend Setup (2 minutes)

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be running at <http://localhost:3000>

## Step 4: Verify Installation

1. Open <http://localhost:3000> in your browser
2. You should see the dashboard (may be empty initially)
3. Backend API docs available at <http://localhost:8000/docs>
4. Wait ~30 seconds for first data collection to begin

## Troubleshooting

### Backend won't start

- Check Python version: `python --version` (need 3.11+)
- Verify all environment variables are set in `.env`
- Check CosmosDB connectivity

### Frontend won't start

- Check Node version: `node --version` (need 18+)
- Clear node_modules: `rm -rf node_modules && npm install`

### No data appearing

- Check backend logs for Reddit API errors
- Verify Reddit API credentials are correct
- First collection cycle takes ~5 minutes to complete

## Next Steps

- Customize monitored subreddits in `.env` → `SUBREDDITS`
- Configure LLM sentiment analysis (optional)
- Review API documentation at `/docs`
- Check the full README.md for deployment options

## Development Tips

- Backend auto-reloads on code changes
- Frontend has hot module replacement
- Use `pytest` for backend tests
- Check logs in backend console for collection status
