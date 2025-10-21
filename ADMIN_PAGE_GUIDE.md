# Admin Page Usage Guide

## Overview

The Admin Tool Approval page (`/admin`) allows administrators to review and approve/reject AI tools that have been auto-detected from Reddit discussions.

## How It Works

### Step 1: Authentication

1. Navigate to `http://localhost:5173/admin`
2. You'll see an admin token input form
3. **Enter ANY text as the admin token** (e.g., "admin", "test", "password")
   - The current implementation accepts any non-empty token
   - In production, this would validate against a real auth system

### Step 2: View Pending Tools

Once authenticated, you'll see:

- **Pending Tools Table**: List of tools awaiting approval
  - Tool Name
  - Description
  - Mention Count (last 7 days)
  - Sample mentions from Reddit
  - Detected date
  - Actions (Approve/Reject buttons)

### Step 3: Approve or Reject Tools

**Approve a Tool:**

- Click the green "✓ Approve" button
- Tool status changes from "pending" → "approved"
- Tool will now appear on the main dashboard
- Sentiment data will be calculated and displayed

**Reject a Tool:**

- Click the red "✗ Reject" button  
- Tool status changes from "pending" → "rejected"
- Tool will NOT appear on dashboard
- Can be useful to filter out false positives

## Current State

### Why Admin Page Appears Empty

The admin page shows pending tools, but you likely don't have any because:

1. **No Tools Are "Pending"**
   - The seed script creates tools with status "approved" (GitHub Copilot, Jules AI)
   - Auto-detection hasn't run yet to create new pending tools

2. **No Auto-Detection Data**
   - Tool detection requires Reddit posts to be collected first
   - Background job scans posts for tool mentions
   - When 50+ mentions found in 7 days → creates pending tool

## How to Test Admin Functionality

### Option 1: Create a Pending Tool Manually (Quick Test)

Run this script to create a test pending tool:

```bash
cd backend
python3 << 'EOF'
import asyncio
from datetime import datetime
from azure.cosmos.aio import CosmosClient
from src.config import settings

async def create_pending_tool():
    async with CosmosClient(settings.cosmos_endpoint, credential=settings.cosmos_key) as client:
        database = client.get_database_client(settings.cosmos_database)
        container = database.get_container_client("ai_tools")
        
        pending_tool = {
            "id": "cursor-editor",
            "name": "Cursor Editor",
            "vendor": "Cursor",
            "category": "AI Assistant",
            "aliases": ["cursor", "cursor editor", "cursor ide"],
            "status": "pending",  # <-- This makes it show in admin panel
            "detection_threshold": 0.7,
            "first_detected_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        await container.upsert_item(pending_tool)
        print("✅ Created pending tool: Cursor Editor")
        print("   Now refresh the admin page with token 'admin'")

asyncio.run(create_pending_tool())
EOF
```

### Option 2: Check Backend Response Directly

Test the admin endpoint:

```bash
# Start backend if not running
cd backend && ./start.sh &

# Wait for startup
sleep 5

# Get pending tools
curl -H "X-Admin-Token: admin" http://localhost:8000/api/v1/admin/tools/pending | python3 -m json.tool
```

**Expected Response (if no pending tools):**

```json
{
  "pending_tools": [],
  "count": 0
}
```

**Expected Response (with pending tools):**

```json
{
  "pending_tools": [
    {
      "id": "cursor-editor",
      "name": "Cursor Editor",
      "status": "pending",
      "description": null,
      "mention_count_7d": 0,
      "sample_mentions": [],
      "first_detected_at": "2025-10-21T15:00:00Z"
    }
  ],
  "count": 1
}
```

### Option 3: Full Integration Test

1. **Create a pending tool** (Option 1 script)
2. **Open admin page**: <http://localhost:5173/admin>
3. **Enter token**: "admin" (or any text)
4. **You should see**: Cursor Editor in the pending tools table
5. **Click "✓ Approve"**: Tool becomes approved
6. **Navigate to main dashboard**: You'll see Cursor Editor sentiment card
7. **Click "✗ Reject"** (or test with another pending tool): Tool is rejected

## Admin Page UI Components

### When Authenticated

```text
┌─────────────────────────────────────────────────────────┐
│  Admin Tool Approval                        [Logout]    │
├─────────────────────────────────────────────────────────┤
│  ✅ Success: Successfully approved "Cursor Editor"      │
│  (or)                                                   │
│  ❌ Error: Failed to approve tool                       │
├─────────────────────────────────────────────────────────┤
│  Pending Tools (2)                          [Refresh]   │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Cursor Editor                                     │ │
│  │ Category: AI Assistant                            │ │
│  │ Mentions (7d): 0                                  │ │
│  │ Detected: 2025-10-21                              │ │
│  │ [✓ Approve]  [✗ Reject]                           │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Claude Code                                       │ │
│  │ ...                                               │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### When NOT Authenticated

```text
┌─────────────────────────────────────────────────────────┐
│  Admin Tool Approval                                    │
│                                                         │
│  Enter your admin token to view and manage              │
│  pending AI tool approvals                              │
│                                                         │
│  Admin Token:                                           │
│  [_______________]   [Submit]                           │
│                                                         │
│  For testing, use any value (e.g., "admin")             │
└─────────────────────────────────────────────────────────┘
```

## Security Notes

⚠️ **Current Implementation** (Development Only):

- Accepts any non-empty token
- No real authentication
- No token validation

✅ **Production Requirements** (TODO):

- Implement OAuth 2.0 or JWT tokens
- Validate tokens against auth service
- Add role-based access control (RBAC)
- Audit log all admin actions
- Token expiration and refresh

## Troubleshooting

### "No pending tools to display"

**Cause**: All tools are either "approved" or "rejected"  
**Fix**: Create a pending tool using Option 1 script above

### "Admin authentication required"

**Cause**: Token not sent in request header  
**Fix**: Make sure you entered a token and clicked Submit

### Admin page shows loading forever

**Cause**: Backend not running  
**Fix**:

```bash
cd backend && ./start.sh
```

### 401 Unauthorized error

**Cause**: Empty or missing token  
**Fix**: Enter any non-empty value as token

## Summary

The Admin page **IS implemented and working**, but appears empty because:

1. ✅ Seeded tools (GitHub Copilot, Jules AI) have status "approved"
2. ❌ No auto-detected tools have status "pending"
3. ⏳ Auto-detection requires Reddit data collection first

**To see the Admin page in action:**
Run the "Option 1" script above to create a pending tool, then visit `/admin` with token "admin".
