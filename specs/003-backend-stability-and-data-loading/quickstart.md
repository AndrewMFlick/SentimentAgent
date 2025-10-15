# Quickstart: Backend Stability and Data Loading

**Feature**: 003-backend-stability-and-data-loading  
**Phase**: 1 (Design)  
**Date**: January 15, 2025

## Overview

This guide shows how to start, monitor, and troubleshoot the SentimentAgent backend with the new stability improvements. The backend now includes graceful shutdown, error recovery, health monitoring, and automatic data loading on startup.

---

## Prerequisites

- Python 3.13.3+
- Azure CosmosDB emulator running on `localhost:8081` (or configured endpoint)
- Reddit API credentials in `.env` file
- Dependencies installed: `pip install -r backend/requirements.txt`

---

## Starting the Backend

### Development Mode (with auto-reload)

```bash
cd backend
./start.sh
```

**What happens**:

1. Cleans up any orphaned processes on port 8000
2. Sets `PYTHONPATH` to include `backend/src`
3. Starts uvicorn with `--reload` flag for hot-reloading
4. Backend initializes:
   - Connects to CosmosDB
   - Starts APScheduler for data collection (every 30 minutes)
   - Loads last 24 hours of data in background (non-blocking)
5. Server ready on `http://localhost:8000`

**Expected Output**:

```
INFO:     Will watch for changes in these directories: ['/Users/.../SentimentAgent/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Database connected
INFO:     Scheduler started
INFO:     Application startup complete.
INFO:     Loaded 1423 recent posts from last 24 hours
```

### Production Mode (systemd)

```bash
# Copy systemd service file
sudo cp deployment/systemd/sentimentagent.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable sentimentagent
sudo systemctl start sentimentagent

# Check status
sudo systemctl status sentimentagent
```

**What happens**:

1. systemd starts backend as a service
2. Automatically restarts on failure (`Restart=always`)
3. No `--reload` flag (production-safe)
4. Logs to journalctl: `sudo journalctl -u sentimentagent -f`

---

## Verifying Backend Health

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

**Expected Response (Healthy)**:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "process": {
    "uptime_seconds": 120,
    "memory_mb": 256.5,
    "cpu_percent": 2.1
  },
  "application": {
    "last_collection_at": "2025-01-15T10:00:00.000Z",
    "collections_succeeded": 2,
    "collections_failed": 0,
    "data_freshness_minutes": 30
  },
  "database": {
    "connected": true
  }
}
```

**Status Meanings**:

- `"healthy"`: All systems operational ✅
- `"degraded"`: Minor issues (stale data, high memory) ⚠️
- `"unhealthy"`: Critical failure (DB disconnected, memory exhausted) ❌

### Manual Health Checks

```bash
# Check process is running
ps aux | grep "python3 -m uvicorn"

# Check port 8000 is listening
lsof -i :8000

# Check memory usage
ps aux | grep "python3 -m uvicorn" | awk '{print $4 "%"}'

# Check database connection
curl http://localhost:8000/health | jq '.database.connected'
```

---

## Data Collection Monitoring

### View Collection Logs

```bash
# Tail logs in development
tail -f backend/logs/app.log

# View systemd logs in production
sudo journalctl -u sentimentagent -f --since "10 minutes ago"
```

**Expected Log Patterns**:

```
INFO: Scheduler started
INFO: Collected 50 posts from r/technology
INFO: Collected 1200 comments for r/technology
INFO: Saved 50 posts to database
INFO: Collection completed successfully for all 14 subreddits
```

### Trigger Manual Collection

```bash
# Option 1: Restart backend (triggers immediate collection)
./start.sh

# Option 2: Use API endpoint (if implemented)
curl -X POST http://localhost:8000/admin/collect-now
```

---

## Troubleshooting

### Backend Won't Start

**Problem**: `Address already in use` error

**Solution**:

```bash
# Kill orphaned processes
pkill -f "python3 -m uvicorn"

# Or manually find and kill
lsof -i :8000
kill -9 <PID>

# Restart
./start.sh
```

---

### Backend Crashes During Collection

**Problem**: Backend stops after data collection

**Diagnosis**:

```bash
# Check exit reason
echo $?  # Exit code (non-zero = crashed)

# Check last logs
tail -50 backend/logs/app.log
```

**Solution**:

1. Check if database is running:
   ```bash
   curl http://localhost:8081/_explorer/index.html
   ```

2. Verify `.env` file exists and has correct values:
   ```bash
   cat backend/.env | grep -E "(COSMOS_|REDDIT_)"
   ```

3. Test Reddit API credentials:
   ```bash
   python3 -c "import praw; r = praw.Reddit(...); print(r.user.me())"
   ```

---

### Database Connection Failures

**Problem**: `/health` shows `"connected": false`

**Diagnosis**:

```bash
# Check CosmosDB emulator is running
curl http://localhost:8081/

# Check connection string in .env
cat backend/.env | grep COSMOS_CONNECTION_STRING
```

**Solution**:

```bash
# Start CosmosDB emulator
# macOS: Open Azure Cosmos DB Emulator app
# Linux: docker run -p 8081:8081 mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator

# Verify connection
curl http://localhost:8081/

# Restart backend
./start.sh
```

---

### High Memory Usage

**Problem**: `/health` shows `"memory_mb": 480` (degraded)

**Diagnosis**:

```bash
# Check memory trend
watch -n 5 'curl -s http://localhost:8000/health | jq .process.memory_mb'
```

**Solution**:

```bash
# Restart backend to clear memory
pkill -f "python3 -m uvicorn"
./start.sh

# If persists, check for memory leaks in logs
grep -i "memory" backend/logs/app.log
```

---

### Stale Data (Freshness > 45 minutes)

**Problem**: `/health` shows `"data_freshness_minutes": 60` (degraded)

**Diagnosis**:

```bash
# Check last collection time
curl -s http://localhost:8000/health | jq '.application.last_collection_at'

# Check scheduler logs
grep "Collection completed" backend/logs/app.log | tail -5
```

**Solution**:

1. **If scheduler stopped**: Restart backend
   ```bash
   ./start.sh
   ```

2. **If Reddit API rate limited**: Wait 10 minutes, check again
   ```bash
   grep "429" backend/logs/app.log
   ```

3. **If network issues**: Check internet connection, retry

---

## Graceful Shutdown

### Stopping Backend Safely

```bash
# Development: Press Ctrl+C in terminal
# Backend will:
# 1. Stop accepting new requests
# 2. Wait for running collection jobs to complete (max 30s)
# 3. Disconnect from database
# 4. Exit cleanly

# Production (systemd):
sudo systemctl stop sentimentagent
```

**Expected Shutdown Logs**:

```
INFO: Shutting down
INFO: Shutting down scheduler...
INFO: Scheduler stopped
INFO: Disconnecting from database
INFO: Finished server process [12346]
```

---

## Performance Benchmarks

### Expected Metrics (Healthy State)

| Metric | Expected Value | Threshold |
|--------|----------------|-----------|
| Uptime | >24 hours | N/A |
| Memory Usage | 200-300 MB | <450 MB (degraded), <500 MB (unhealthy) |
| CPU (idle) | 0-5% | N/A |
| CPU (collecting) | 10-30% | N/A |
| Data Freshness | <35 minutes | <45 min (degraded), <120 min (unhealthy) |
| Collection Success Rate | >95% | >90% (degraded) |

### Load Testing

```bash
# Install dependencies
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

---

## Monitoring in Production

### Prometheus Integration (Optional)

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'sentimentagent'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/health'
    scrape_interval: 30s
```

### Alerting Rules

```yaml
groups:
  - name: sentimentagent
    rules:
      - alert: BackendUnhealthy
        expr: sentimentagent_health_status == 2  # unhealthy
        for: 5m
        annotations:
          summary: "SentimentAgent backend is unhealthy"
      
      - alert: StaleData
        expr: sentimentagent_data_freshness_minutes > 60
        for: 10m
        annotations:
          summary: "Data collection stalled"
```

---

## FAQ

**Q: How long does startup take?**

A: ~5-10 seconds for app initialization. Background data loading completes within 1-2 minutes (non-blocking).

**Q: What happens if collection fails for one subreddit?**

A: Scheduler logs the error and continues with remaining subreddits. Check `/health` for failure count.

**Q: Can I change collection interval?**

A: Yes, edit `backend/src/config.py`:
```python
COLLECTION_INTERVAL_MINUTES = 30  # Change to desired interval
```

**Q: How do I view OpenAPI docs?**

A: Visit `http://localhost:8000/docs` (Swagger UI)

**Q: How do I reset application state?**

A: Restart backend:
```bash
pkill -f "python3 -m uvicorn"
./start.sh
```

---

## Next Steps

- **Development**: Start backend with `./start.sh` and monitor `/health`
- **Production**: Set up systemd service and configure monitoring
- **Testing**: Run `pytest backend/tests/` to validate stability

For detailed troubleshooting, see [TROUBLESHOOTING.md](../../../TROUBLESHOOTING.md).
