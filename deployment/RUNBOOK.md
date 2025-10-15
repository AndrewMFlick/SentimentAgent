# Production Runbook: SentimentAgent Backend

## Overview

This runbook provides operational procedures for managing the SentimentAgent backend in production.

## Quick Reference

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Start Backend
```bash
cd backend
./start.sh
```

### Stop Backend
```bash
pkill -f "uvicorn.*src.main:app"
```

### View Logs
```bash
# Follow logs in real-time
tail -f /var/log/sentimentagent/backend.log

# Search for errors
grep -i error /var/log/sentimentagent/backend.log | tail -20
```

## Common Scenarios

### 1. Backend Crashes or Stops Responding

**Symptoms**:
- Health endpoint returns no response or connection refused
- Frontend shows "API unavailable" error
- No recent collection logs

**Diagnosis**:
1. Check if process is running:
   ```bash
   ps aux | grep uvicorn
   ```

2. Check recent logs for errors:
   ```bash
   tail -50 /var/log/sentimentagent/backend.log | grep -i error
   ```

3. Check system resources:
   ```bash
   free -h  # Memory
   df -h    # Disk space
   ```

**Resolution**:
1. Restart backend:
   ```bash
   cd /path/to/backend
   ./start.sh
   ```

2. Wait 30 seconds, then verify health:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

3. Monitor for 5 minutes to ensure stability:
   ```bash
   watch -n 10 'curl -s http://localhost:8000/api/v1/health | jq'
   ```

**Prevention**:
- Set up systemd service for automatic restart (see deployment/systemd/)
- Monitor memory usage and set alerts at 400MB
- Set up external monitoring with process_monitor.py

### 2. Data Collection Failing

**Symptoms**:
- `collections_failed` counter increasing in health response
- No new data in database
- Error logs showing Reddit API failures

**Diagnosis**:
1. Check health endpoint:
   ```bash
   curl http://localhost:8000/api/v1/health | jq '.application'
   ```

2. Check last collection time:
   ```json
   {
     "last_collection_at": "2025-10-15T10:00:00Z",
     "collections_succeeded": 10,
     "collections_failed": 5,
     "data_freshness_minutes": 120
   }
   ```

3. Review error logs:
   ```bash
   grep "Collection cycle" /var/log/sentimentagent/backend.log | tail -10
   ```

**Resolution**:
1. **Reddit API Rate Limiting**:
   - Wait 10 minutes for rate limit to reset
   - Reduce `COLLECTION_INTERVAL_MINUTES` if needed
   - Verify Reddit credentials in `.env`

2. **Database Connection Issues**:
   - Check database connectivity:
     ```bash
     curl http://localhost:8000/api/v1/health | jq '.database.connected'
     ```
   - Verify CosmosDB endpoint and key in `.env`
   - Check network connectivity to CosmosDB

3. **Trigger Manual Collection** (for testing):
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/collect
   ```

**Prevention**:
- Set up monitoring alerts for `collections_failed` > 3
- Monitor `data_freshness_minutes` and alert if > 60

### 3. High Memory Usage

**Symptoms**:
- Health endpoint shows `memory_mb` > 400
- Backend status is "degraded"
- System swap usage increasing

**Diagnosis**:
1. Check current memory:
   ```bash
   curl http://localhost:8000/api/v1/health | jq '.process.memory_mb'
   ```

2. Check memory delta in collection logs:
   ```bash
   grep "memory_delta" /var/log/sentimentagent/backend.log | tail -5
   ```

3. Look for memory leaks:
   ```bash
   # Compare memory before and after collection cycles
   watch -n 300 'curl -s http://localhost:8000/api/v1/health | jq .process.memory_mb'
   ```

**Resolution**:
1. **Immediate** (if memory > 450MB):
   - Restart backend to free memory
   ```bash
   cd /path/to/backend
   ./start.sh
   ```

2. **Investigate**:
   - Check if memory increases continuously
   - Review collection cycle logs for large datasets
   - Reduce `COLLECTION_INTERVAL_MINUTES` to allow garbage collection

3. **Long-term**:
   - Add pagination limits to database queries
   - Reduce number of monitored subreddits
   - Optimize data models

**Prevention**:
- Set memory alerts at 400MB (degraded) and 480MB (critical)
- Monitor `memory_delta` in collection logs
- Schedule weekly backend restarts during low-usage periods

### 4. Database Connection Lost

**Symptoms**:
- Health endpoint returns 503 status
- `database.connected: false` in health response
- Backend status is "unhealthy"

**Diagnosis**:
1. Check database status:
   ```bash
   curl http://localhost:8000/api/v1/health
   # Returns 503 if database disconnected
   ```

2. Test CosmosDB connectivity:
   ```bash
   curl -k https://your-cosmos-endpoint.documents.azure.com:443/
   ```

3. Check network and firewall rules

**Resolution**:
1. **Verify Credentials**:
   - Check `COSMOS_ENDPOINT` and `COSMOS_KEY` in `.env`
   - Ensure credentials haven't expired

2. **Network Issues**:
   - Check firewall rules
   - Verify CosmosDB is accessible from backend server
   - Check CosmosDB service health in Azure portal

3. **Restart Backend**:
   - Backend will attempt to reconnect on startup
   ```bash
   cd /path/to/backend
   ./start.sh
   ```

**Prevention**:
- Set up CosmosDB availability monitoring
- Configure retry logic (already implemented with exponential backoff)
- Monitor database connection status

### 5. No Data in Frontend

**Symptoms**:
- Frontend displays zeros or "No data available"
- API endpoints return empty arrays
- Backend is healthy and collecting data

**Diagnosis**:
1. Verify backend health:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. Check if data exists:
   ```bash
   curl "http://localhost:8000/api/v1/posts/recent?limit=5"
   curl "http://localhost:8000/api/v1/sentiment/stats?hours=24"
   ```

3. Check data freshness:
   ```bash
   curl http://localhost:8000/api/v1/health | jq '.application.data_freshness_minutes'
   ```

**Resolution**:
1. **No Data Loaded After Restart**:
   - Wait for startup data loading to complete (check logs)
   - Trigger manual collection:
     ```bash
     curl -X POST http://localhost:8000/api/v1/admin/collect
     ```

2. **Data Too Old**:
   - Frontend queries default to last 24 hours
   - Try wider time window:
     ```bash
     curl "http://localhost:8000/api/v1/sentiment/stats?hours=168"
     ```

3. **CORS Issues**:
   - Check browser console for CORS errors
   - Verify `API_CORS_ORIGINS` in backend `.env`

**Prevention**:
- Monitor `data_freshness_minutes` and alert if > 60
- Verify startup data loading completes successfully

## Monitoring Setup

### External Process Monitor

Run the external monitor in a separate terminal or as a background service:

```bash
cd backend
nohup python3 monitoring/process_monitor.py --interval 60 > /var/log/sentimentagent/monitor.log 2>&1 &
```

### Health Check Monitoring

Add to cron for periodic health checks:

```bash
# Check every 5 minutes
*/5 * * * * curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1 || echo "Backend unhealthy" | mail -s "SentimentAgent Alert" admin@example.com
```

### Log Rotation

Configure logrotate for backend logs:

```
/var/log/sentimentagent/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 sentimentagent sentimentagent
}
```

## Metrics to Monitor

### Critical Metrics (Alert Immediately)
- Backend process not running
- Database connection status: false
- Health endpoint returns 503
- Memory usage > 480MB

### Warning Metrics (Investigate Soon)
- `collections_failed` > 3 in last hour
- `data_freshness_minutes` > 60
- Memory usage > 400MB
- CPU usage > 80% sustained

### Information Metrics (Track Trends)
- `collections_succeeded` count
- Average response times
- Memory delta per collection cycle

## Escalation

1. **Level 1** (Self-service):
   - Restart backend
   - Check logs for obvious errors
   - Verify configuration

2. **Level 2** (Support):
   - Review application logs in detail
   - Check Azure service health
   - Investigate database performance

3. **Level 3** (Development):
   - Code-level debugging
   - Performance profiling
   - Architecture changes

## Useful Commands

```bash
# Check backend version/commit
cd backend && git log -1 --oneline

# Count recent errors
grep -i error /var/log/sentimentagent/backend.log | grep "$(date +%Y-%m-%d)" | wc -l

# Monitor collection cycles
tail -f /var/log/sentimentagent/backend.log | grep "Collection cycle"

# Check database queries
grep "Query" /var/log/sentimentagent/backend.log | tail -20

# Find slow queries
grep "slow" /var/log/sentimentagent/backend.log

# Check system resources
top -b -n 1 | grep -i python
free -h
df -h
```

## Recovery Procedures

### Complete System Restart

```bash
# 1. Stop all services
pkill -f "uvicorn.*src.main:app"

# 2. Wait for cleanup
sleep 5

# 3. Verify all stopped
ps aux | grep uvicorn

# 4. Clear any orphaned processes
pkill -9 -f "uvicorn.*src.main:app"

# 5. Start backend
cd /path/to/backend
./start.sh

# 6. Verify health
sleep 10
curl http://localhost:8000/api/v1/health

# 7. Monitor for 5 minutes
watch -n 30 'curl -s http://localhost:8000/api/v1/health | jq'
```

### Database Emergency

If database is unavailable but backend must stay running:
- Backend will mark status as "unhealthy" (503 response)
- Collection will fail but backend won't crash
- Once database is restored, backend will automatically reconnect
- May need to restart backend to re-establish connection

## Contact Information

- **On-call Engineer**: [Contact info]
- **Azure Support**: [Support number]
- **CosmosDB Team**: [Team contact]
- **Documentation**: `/docs` directory

## Change Log

- 2025-10-15: Initial runbook created
- Added health monitoring procedures
- Added backend stability features
