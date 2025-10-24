#!/bin/bash
# Script to clean up all reanalysis jobs from the database
# Useful for testing and development

API_URL="http://localhost:8000/api/v1/admin/reanalysis"
ADMIN_TOKEN="admin-secret-token-2024"

echo "=== Reanalysis Jobs Cleanup Script ==="
echo ""

# List all jobs
echo "1. Fetching all jobs..."
JOBS_JSON=$(curl -s -H "X-Admin-Token: $ADMIN_TOKEN" "$API_URL/jobs")

# Extract job IDs and statuses
JOB_IDS=$(echo "$JOBS_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for job in data.get('jobs', []):
    print(f\"{job['id']}|{job['status']}\")
")

if [ -z "$JOB_IDS" ]; then
    echo "✅ No jobs found. Database is clean."
    exit 0
fi

echo "Found jobs:"
echo "$JOB_IDS" | while IFS='|' read -r job_id status; do
    echo "  - $job_id ($status)"
done
echo ""

# Cancel all queued/running jobs
echo "2. Cancelling queued/running jobs..."
CANCELLED=0
echo "$JOB_IDS" | while IFS='|' read -r job_id status; do
    if [ "$status" = "queued" ] || [ "$status" = "running" ]; then
        echo -n "  Cancelling $job_id... "
        RESULT=$(curl -s -X DELETE -H "X-Admin-Token: $ADMIN_TOKEN" "$API_URL/jobs/$job_id")
        if echo "$RESULT" | grep -q "cancelled successfully"; then
            echo "✅ Done"
            CANCELLED=$((CANCELLED + 1))
        else
            echo "❌ Failed: $RESULT"
        fi
    fi
done

echo ""
echo "=== Cleanup Complete ==="
echo "Cancelled: $CANCELLED job(s)"
echo ""

# List final state
echo "Final state:"
curl -s -H "X-Admin-Token: $ADMIN_TOKEN" "$API_URL/jobs" | python3 -m json.tool
