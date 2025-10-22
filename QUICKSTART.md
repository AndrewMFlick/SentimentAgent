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
ADMIN_TOKEN=your_secure_admin_token_here
```

**Using CosmosDB Emulator for Development:**

```env
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
ADMIN_TOKEN=dev-admin-token-123
```

**Required CosmosDB Containers:**

The application expects these containers in your database:

- `Tools` (partition key: `/id`)
- `ToolAliases` (partition key: `/id`)
- `Sentiments` (partition key: `/tool_id`)
- `AdminActions` (partition key: `/id`)

These will be created automatically on first run if using the emulator.

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

## Step 5: Admin Tool Management Setup (Optional)

The admin panel allows you to manage tools tracked for sentiment analysis.

1. Navigate to the Admin section in the UI (requires `ADMIN_TOKEN`)
2. Initial setup will show an empty tool list
3. Add your first tool:
   - Click "Add Tool"
   - Enter tool name (e.g., "GitHub Copilot")
   - Select category (e.g., "Code Assistant")
   - Specify vendor (e.g., "GitHub")
4. View sentiment data as it collects over time

**Admin Features:**

- Create/Edit/Archive/Delete tools
- Merge duplicate tools (preserves sentiment history)
- View merge history and audit logs
- Export tool data (CSV)

## Troubleshooting

### Backend won't start

- Check Python version: `python --version` (need 3.11+)
- Verify all environment variables are set in `.env`
- Check CosmosDB connectivity
- **CosmosDB emulator not running**: Start the emulator first
- **Port 8000 already in use**: Stop other processes or change port in `src/main.py`

### Frontend won't start

- Check Node version: `node --version` (need 18+)
- Clear node_modules: `rm -rf node_modules && npm install`
- **Port 3000 already in use**: Vite will suggest an alternative port automatically
- **TypeScript errors**: Run `npm run build` to check for compilation issues

### No data appearing

- Check backend logs for Reddit API errors
- Verify Reddit API credentials are correct
- First collection cycle takes ~5 minutes to complete
- **Empty dashboard**: Ensure Tools are created in admin panel
- **Sentiment data not updating**: Check scheduler logs in backend console

### Admin panel issues

- **"Unauthorized" errors**: Verify `ADMIN_TOKEN` in `.env` matches the token in your request headers
- **Tools not saving**: Check CosmosDB containers exist (Tools, ToolAliases)
- **Merge operation fails**: Ensure target tool exists and source tools are valid
- **Cannot delete tool**: Archive the tool first if it has sentiment data

### Database connection issues

- **Local emulator**: Ensure CosmosDB emulator is running on port 8081
- **Azure production**: Verify `COSMOS_ENDPOINT` and `COSMOS_KEY` are correct
- **SSL certificate errors**: Add `-n` flag when starting emulator or disable SSL verification (dev only)
- **Slow queries**: Check performance logs for queries exceeding 3 seconds

### Performance issues

- **Slow UI loading**: Enable skeleton loaders (already implemented)
- **Backend memory usage high**: Reduce `SUBREDDITS` count or collection frequency
- **Frontend bundle size**: Run `npm run build` and check bundle analysis

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
