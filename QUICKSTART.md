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

1. **Check Health**: Open <http://localhost:8000/api/v1/health>
   - Should return `{"status": "healthy"}`
   - Verify database connection is `true`
   - Check process PID and uptime

2. **Open Dashboard**: Navigate to <http://localhost:3000>
   - Dashboard should load (may be empty initially)
   - API docs available at <http://localhost:8000/docs>

3. **Wait for Data Collection**:
   - First collection starts ~30 seconds after backend startup
   - Check backend logs for "Data collection" messages
   - Posts should appear in dashboard after first collection (~5 minutes)

4. **Verify Database Setup**:
   ```bash
   # Check if containers exist
   curl http://localhost:8000/api/v1/health
   ```
   
   Required containers should be created automatically:
   - `reddit_posts`, `reddit_comments`, `sentiment_scores`
   - `trending_topics`, `Tools`, `ToolAliases`
   - `AdminActions`, `ReanalysisJobs` (for Feature 013)

5. **Test Reanalysis Feature** (Optional but recommended):
   ```bash
   # Trigger a test reanalysis job
   curl -X POST http://localhost:8000/api/v1/admin/reanalysis/jobs \
     -H "Content-Type: application/json" \
     -H "X-Admin-Token: your-admin-token" \
     -d '{"batch_size": 50}'
   
   # Check job status (replace {job_id} with response from above)
   curl -H "X-Admin-Token: your-admin-token" \
     http://localhost:8000/api/v1/admin/reanalysis/jobs/{job_id}/status
   
   # Should return status: "queued" then "running" then "completed"
   # Verify sentiment_scores documents updated with detected_tool_ids
   ```

6. **Test Frontend UI**:
   - Navigate to <http://localhost:3000/admin>
   - Enter admin token from `.env`
   - Click "Reanalysis Jobs" tab
   - Should see job history and monitoring UI

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

### Reanalysis job issues

- **400 "Cannot start job: X job(s) already active"**: 
  - Only one reanalysis job can run at a time
  - List active jobs: `curl -H "X-Admin-Token: token" http://localhost:8000/api/v1/admin/reanalysis/jobs?status=queued`
  - Cancel if needed: `curl -X DELETE -H "X-Admin-Token: token" http://localhost:8000/api/v1/admin/reanalysis/jobs/{job_id}`

- **Job stuck in "queued" status**:
  - Check backend logs for scheduler errors
  - Job poller runs every 60 seconds
  - Restart backend if scheduler isn't running

- **Slow reanalysis performance**:
  - Reduce batch delay: `REANALYSIS_BATCH_DELAY_MS=50` in `.env`
  - Increase batch size: `{"batch_size": 200}` in API request
  - Check CosmosDB metrics for throttling

- **CosmosDB 429 rate limit errors**:
  - System automatically retries with exponential backoff
  - Increase delay if errors persist: `REANALYSIS_BATCH_DELAY_MS=200`
  - Increase max retries: `REANALYSIS_MAX_RETRIES=10`

- **Sentiment scores not updated after reanalysis**:
  - Check job statistics: `GET /api/v1/admin/reanalysis/jobs/{job_id}`
  - Look for `errors_count` in response
  - Common issues: missing content field, no matching tools, database permissions

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
