# UI Testing Guide - Reanalysis Jobs Feature (T041)

## Overview
This guide provides step-by-step instructions for manually testing the reanalysis jobs monitoring UI in the admin dashboard.

## Prerequisites

### 1. Start Backend Server
```bash
cd backend
python3 -m src.main
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
Data loading complete: XXX posts, XXX comments, XXX sentiment scores loaded
```

**Verify backend is healthy:**
```bash
curl http://localhost:8000/api/v1/health
```

### 2. Start Frontend Server
```bash
cd frontend
npm run dev
```

**Expected output:**
```
VITE v5.4.20  ready in XXX ms

➜  Local:   http://localhost:3000/
```

## Test Scenarios

### Scenario 1: Access Admin Dashboard

1. **Navigate to Admin Panel**
   - Open browser: `http://localhost:3000/admin`
   - Enter admin token: `admin-secret-token-2024`
   - Click "Unlock Admin Panel"

2. **Expected Result:**
   - ✅ Admin panel unlocks successfully
   - ✅ Multiple tabs visible: Tool Management, Reanalysis Jobs
   - ✅ Glass morphism UI with dark theme

### Scenario 2: View Empty Reanalysis Jobs List

1. **Navigate to Reanalysis Jobs Tab**
   - Click "Reanalysis Jobs" tab

2. **Expected Result:**
   - ✅ "Trigger Reanalysis Job" button visible
   - ✅ Job monitor table showing "No reanalysis jobs yet"
   - ✅ Empty state message displayed

### Scenario 3: Create a Reanalysis Job

1. **Open Trigger Form**
   - Click "Trigger Reanalysis Job" button

2. **Fill Form with Basic Settings**
   - Batch Size: `50`
   - Leave date range empty
   - Leave tool filters empty

3. **Submit Job**
   - Click "Trigger Reanalysis" button

4. **Expected Result:**
   - ✅ Success notification appears
   - ✅ Modal closes automatically
   - ✅ New job appears in monitor table
   - ✅ Job status shows "QUEUED" with blue badge
   - ✅ Progress bar at 0%
   - ✅ ETA calculated and displayed

### Scenario 4: Monitor Job Progress

1. **Observe Auto-Refresh**
   - Wait and watch the job monitor table
   - Auto-refresh should poll every 5 seconds

2. **Expected Result:**
   - ✅ Status updates automatically (QUEUED → RUNNING → COMPLETED)
   - ✅ Progress bar animates from 0% to 100%
   - ✅ "Processed" count increases
   - ✅ ETA countdown updates
   - ✅ Green badge when completed

### Scenario 5: Create Job with Date Range Filter

1. **Open Trigger Form**
   - Click "Trigger Reanalysis Job" button

2. **Fill Form with Date Filter**
   - Batch Size: `50`
   - Start Date: Select 7 days ago
   - End Date: Select today

3. **Submit and Verify**
   - Click "Trigger Reanalysis"
   - Check "Estimated Documents" in response

4. **Expected Result:**
   - ✅ Job created with date range
   - ✅ Estimated documents shows filtered count
   - ✅ Job appears in monitor with date range displayed

### Scenario 6: Create Job with Tool Filter

1. **Open Trigger Form**
   - Click "Trigger Reanalysis Job" button

2. **Fill Form with Tool Filter**
   - Batch Size: `100`
   - Tool Filters: Select "Copilot"

3. **Submit and Verify**
   - Click "Trigger Reanalysis"

4. **Expected Result:**
   - ✅ Job created with tool filter
   - ✅ Only Copilot mentions will be reanalyzed
   - ✅ Estimated documents reflects filter

### Scenario 7: Test Job Cancellation

1. **Create a Job**
   - Create a new job with batch size 10

2. **Cancel While Queued**
   - Click "Cancel" button in the job row
   - Confirm cancellation in modal

3. **Expected Result:**
   - ✅ Confirmation modal appears
   - ✅ After confirmation, status changes to "CANCELLED"
   - ✅ Red badge displayed
   - ✅ Cancel button becomes disabled

### Scenario 8: Test Concurrent Job Prevention

1. **Create First Job**
   - Trigger a job with batch size 50

2. **Try Creating Second Job**
   - While first job is queued/running, try to create another job

3. **Expected Result:**
   - ✅ Error notification: "Cannot start job: 1 job(s) already active"
   - ✅ HTTP 400 response
   - ✅ Only one job active at a time

### Scenario 9: View Job Details

1. **Expand Job Row**
   - Click on a job row in the monitor table

2. **Expected Result:**
   - ✅ Details section expands
   - ✅ Shows: Job ID, Created At, Updated At, Triggered By
   - ✅ Shows filters applied (date range, tools)
   - ✅ Error log (if any errors occurred)

### Scenario 10: Test Pagination

1. **Create Multiple Jobs**
   - Create and cancel several jobs to accumulate history

2. **Navigate Pages**
   - Use pagination controls at bottom of table
   - Try "Previous", "Next", and page number buttons

3. **Expected Result:**
   - ✅ Table shows 10 jobs per page
   - ✅ Pagination controls work correctly
   - ✅ Page numbers update
   - ✅ Total count displayed

## API Testing (Command Line)

### Create Job
```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Admin-Token: admin-secret-token-2024" \
     -d '{"batch_size":50}' \
     http://localhost:8000/api/v1/admin/reanalysis/jobs
```

**Expected Response:**
```json
{
  "job_id": "uuid-here",
  "status": "queued",
  "estimated_docs": 0,
  "message": "Reanalysis job queued successfully",
  "poll_url": "/admin/reanalysis/jobs/{job_id}/status"
}
```

### List Jobs
```bash
curl -H "X-Admin-Token: admin-secret-token-2024" \
     http://localhost:8000/api/v1/admin/reanalysis/jobs
```

### Get Job Status
```bash
curl -H "X-Admin-Token: admin-secret-token-2024" \
     http://localhost:8000/api/v1/admin/reanalysis/jobs/{job_id}/status
```

### Cancel Job
```bash
curl -X DELETE -H "X-Admin-Token: admin-secret-token-2024" \
     http://localhost:8000/api/v1/admin/reanalysis/jobs/{job_id}
```

## Known Issues

### CosmosDB Emulator COUNT Bug (FIXED)
- **Issue:** COUNT queries returned stale/cached results
- **Fix:** Replaced `SELECT VALUE COUNT(1)` with `SELECT *` + `len()` in Python
- **Affected:** `check_active_jobs()`, job listing pagination
- **Status:** ✅ Resolved in commit 8aa218c

### Validation Results

| Test Scenario | Status | Notes |
|--------------|--------|-------|
| API endpoints | ✅ Pass | All CRUD operations working |
| UI rendering | ✅ Pass | Glass morphism design correct |
| Auto-refresh | ✅ Pass | 5-second polling functional |
| Job creation | ✅ Pass | With/without filters |
| Job cancellation | ✅ Pass | Only queued jobs |
| Concurrent jobs | ✅ Pass | Correctly prevents duplicates |
| Error handling | ✅ Pass | Appropriate error messages |

## Troubleshooting

### Backend Not Starting
```bash
# Check if port 8000 is in use
lsof -ti:8000

# Kill existing process
lsof -ti:8000 | xargs kill -9

# Restart backend
cd backend && python3 -m src.main
```

### Frontend Not Loading
```bash
# Check if port 3000/5173 is in use
lsof -ti:3000

# Restart frontend
cd frontend && npm run dev
```

### Database Connection Issues
```bash
# Verify CosmosDB emulator is running
curl http://localhost:8081/

# Restart emulator if needed
# (See CosmosDB emulator documentation)
```

## Completion Checklist

- [x] Backend API endpoints tested
- [x] Frontend UI components tested
- [x] Auto-refresh polling verified
- [x] Job creation workflow validated
- [x] Job cancellation tested
- [x] Error handling confirmed
- [x] CosmosDB COUNT bug fixed
- [x] Test jobs cleaned up
- [x] Documentation updated

## Phase 5 Status: ✅ COMPLETE

All tasks (T030-T041) have been implemented and validated.
