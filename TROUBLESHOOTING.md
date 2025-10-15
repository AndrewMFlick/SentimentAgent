# Troubleshooting: Backend and Frontend Data Display

## Current Status

✅ **Backend Stability**: Improved with graceful shutdown and error recovery
✅ **Data Loading**: Existing data loads on startup
✅ **Health Monitoring**: Comprehensive health endpoint available
✅ **Data Collection Working**: Posts and comments are being collected successfully
✅ **Database Saving Working**: All data is being saved to CosmosDB
❓ **UI Data Display**: Verify frontend connection and data flow

## New Features (Backend Stability Release)

### Health Monitoring Endpoint

Check backend health and metrics:
```bash
curl http://localhost:8000/api/v1/health
```

**Response includes**:
- Process uptime, memory usage, CPU percentage
- Collections succeeded/failed counters
- Last collection timestamp
- Data freshness (minutes since last collection)
- Database connection status

**Status codes**:
- `200`: Healthy (all systems operational)
- `503`: Unhealthy (database disconnected or critical failure)

### Backend Stability Features

1. **Graceful Shutdown**: Scheduler waits for running jobs to complete
2. **Catch-Log-Continue**: Collection errors don't crash the backend
3. **Memory Monitoring**: Tracks memory usage per collection cycle
4. **Error Logging**: Full context including stack traces
5. **Retry Logic**: Database operations retry with exponential backoff
6. **Data Loading**: Recent data loads on startup (non-blocking)

## Issues and Solutions

### 1. Backend Process Management

**Problem**: The backend process stops unexpectedly after data collection.

**Solution Implemented**:
- Graceful shutdown handling (scheduler.shutdown(wait=True))
- Error recovery with catch-log-continue pattern
- Process cleanup in start.sh script
- Fail-fast startup (crashes if database unavailable)

**Start backend**:
```bash
cd backend
./start.sh
```

**Monitor backend**:
```bash
# Watch health status
watch -n 5 'curl -s http://localhost:8000/api/v1/health | jq'

# Or use the monitoring script
python3 monitoring/process_monitor.py
```

### 2. Backend Crashes During Collection

**Symptoms**:
- Backend stops responding
- Process terminates unexpectedly
- Orphaned processes

**Debug steps**:
1. Check health endpoint: `curl http://localhost:8000/api/v1/health`
2. Check backend logs for error patterns
3. Verify memory usage: Look for `memory_mb` in health response
4. Check collections_failed counter

**Solutions**:
- Backend now logs all errors with full context
- Collection errors for individual subreddits don't crash entire process
- Memory usage logged at start/end of each cycle

### 3. No Data Showing After Backend Restart

**Problem**: Data exists in database but doesn't show immediately after restart.

**Solution Implemented**:
- `load_recent_data()` runs on startup (background, non-blocking)
- Loads last 24 hours of posts/comments
- Logs loading progress: "Data loading complete: X posts, Y comments loaded in Z seconds"

**Verify**:
```bash
# Check if data loaded
curl "http://localhost:8000/api/v1/sentiment/stats?hours=24"

# Check recent posts
curl "http://localhost:8000/api/v1/posts/recent?limit=10"
```

### 4. Configuration File Path
**Fixed**: Updated `backend/src/config.py` to use absolute path for .env file:
```python
env_file=str(Path(__file__).parent.parent / ".env")
```

### 3. Data Query Time Windows
**Problem**: API queries filter by `collected_at` timestamp (last 24 hours by default), but you may need longer windows.

**Test**: Try different time windows:
```bash
# 24 hours (default)
curl http://localhost:8000/api/v1/sentiment/stats

# 7 days (maximum)
curl "http://localhost:8000/api/v1/sentiment/stats?hours=168"

# Check specific subreddit
curl "http://localhost:8000/api/v1/sentiment/stats?subreddit=Cursor&hours=168"
```

## Recommended Startup Process

### Step 1: Start Backend
```bash
cd /Users/andrewflick/Documents/SentimentAgent/backend
export PYTHONPATH=/Users/andrewflick/Documents/SentimentAgent/backend
python3 -m src.main
```

**Expected output**:
- INFO: Application started successfully
- INFO: Scheduler started - collecting data every 30 minutes
- INFO: Uvicorn running on http://0.0.0.0:8000

**Wait for**: Initial collection cycle to complete (about 5-10 minutes)
**Look for**: "Collection cycle completed: 700 posts, 4000+ comments, 0 errors"

### Step 2: Verify API
```bash
# In a new terminal
curl http://localhost:8000/api/v1/health

# Check sentiment stats
curl "http://localhost:8000/api/v1/sentiment/stats?hours=24"

# Check posts
curl "http://localhost:8000/api/v1/posts/recent?limit=5"
```

### Step 3: Start Frontend
```bash
# In another terminal
cd /Users/andrewflick/Documents/SentimentAgent/frontend
npm run dev
```

**Expected**: Frontend running at http://localhost:3000 or http://localhost:5173

### Step 4: Verify Frontend Connection
1. Open browser to http://localhost:3000 (or http://localhost:5173)
2. Open browser console (F12)
3. Check for API connection errors
4. Look at Network tab to see API requests

## Common Issues

### Issue: "No data showing in UI"

**Check**:
1. Is backend running? `curl http://localhost:8000/api/v1/health`
2. Has collection completed? Look for "Collection cycle completed" in backend logs
3. Is frontend connecting to correct backend? Check `frontend/src/services/api.ts`
4. Are there CORS errors? Check browser console

**Debug API directly**:
```bash
# Get stats
curl -s http://localhost:8000/api/v1/sentiment/stats | python3 -m json.tool

# Get recent posts
curl -s "http://localhost:8000/api/v1/posts/recent?limit=3" | python3 -m json.tool

# Get subreddits being monitored  
curl -s http://localhost:8000/api/v1/subreddits | python3 -m json.tool
```

### Issue: "Backend keeps stopping"

**Possible causes**:
1. Collection process is blocking too long (should be fixed with async improvements)
2. Memory issues during large collections
3. PRAW rate limiting causing crashes
4. CosmosDB connection issues

**Solution**: Run in foreground to see error messages, don't background the process

### Issue: "Port 8000 already in use"

**Fix**:
```bash
# Find and kill process
lsof -i :8000 | grep LISTEN
kill -9 <PID>

# Or kill all Python backend processes
pkill -f "python3 -m src.main"
```

## Verification Checklist

Before assuming "no data":

- [ ] Backend process is running (check with `curl http://localhost:8000/api/v1/health`)
- [ ] At least one collection cycle has completed (check backend logs)
- [ ] API returns data (test with curl commands above)
- [ ] Frontend is running and accessible
- [ ] Frontend console shows no CORS or connection errors
- [ ] Tried different time windows (hours=24, hours=168)

## Next Steps

1. **Keep backend running in foreground** - Don't background it so you can see any errors
2. **Wait for full collection cycle** - Takes 5-10 minutes for first batch
3. **Test API directly with curl** - Verify data exists before checking UI
4. **Check frontend console** - Look for JavaScript errors or API connection issues

## Files Modified

- `backend/src/config.py` - Fixed .env file path resolution
- `backend/start.sh` - Created startup script (optional)

## Data Collection Stats

Latest successful collection:
- **700 posts** collected across 14 subreddits
- **4,000+ comments** processed
- **0 errors** during collection
- All data saved to CosmosDB successfully

The data EXISTS - we just need to ensure the backend stays running and the UI can fetch it!
