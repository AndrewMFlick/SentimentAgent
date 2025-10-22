# Phase 5: Tool Management Dashboard - Testing Guide

## Backend API Testing

### Prerequisites
- Backend server running on http://localhost:8000
- Admin token for authentication

### Endpoints to Test

#### 1. List Tools (GET /api/admin/tools)

**Test: Basic list**
```bash
curl -X GET "http://localhost:8000/api/admin/tools?page=1&limit=20" \
  -H "X-Admin-Token: your-token"
```

**Test: Search by name**
```bash
curl -X GET "http://localhost:8000/api/admin/tools?search=github" \
  -H "X-Admin-Token: your-token"
```

**Test: Filter by category**
```bash
curl -X GET "http://localhost:8000/api/admin/tools?category=code-completion" \
  -H "X-Admin-Token: your-token"
```

**Expected Response:**
```json
{
  "tools": [...],
  "total": 10,
  "page": 1,
  "limit": 20
}
```

#### 2. Update Tool (PUT /api/admin/tools/{tool_id})

**Test: Update tool name**
```bash
curl -X PUT "http://localhost:8000/api/admin/tools/{TOOL_ID}" \
  -H "X-Admin-Token: your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Tool Name",
    "description": "Updated description"
  }'
```

**Expected Response:**
```json
{
  "tool": {...},
  "message": "Tool updated successfully"
}
```

#### 3. Delete Tool (DELETE /api/admin/tools/{tool_id})

**Test: Soft delete (default)**
```bash
curl -X DELETE "http://localhost:8000/api/admin/tools/{TOOL_ID}" \
  -H "X-Admin-Token: your-token"
```

**Test: Hard delete**
```bash
curl -X DELETE "http://localhost:8000/api/admin/tools/{TOOL_ID}?hard_delete=true" \
  -H "X-Admin-Token: your-token"
```

**Expected Response:**
```json
{
  "message": "Tool 'Tool Name' deleted successfully (soft)",
  "tool_id": "..."
}
```

## Frontend UI Testing

### Manual Test Checklist

#### Tab Navigation
- [ ] "Pending Approvals" tab displays correctly
- [ ] "Manage Tools" tab displays correctly
- [ ] Tab switching works smoothly
- [ ] Active tab is visually highlighted

#### Tool Table
- [ ] Table displays all tools
- [ ] Columns show: Name, Vendor, Category, Status, Actions
- [ ] Tool descriptions appear below names (if present)
- [ ] Status badges have correct colors (active=green, deprecated=yellow, deleted=red)

#### Search Functionality
- [ ] Search input is visible and accessible
- [ ] Typing in search box filters results (with debounce)
- [ ] Search matches tool names
- [ ] Clear search shows all tools
- [ ] Page resets to 1 when searching

#### Category Filter
- [ ] Category dropdown shows all categories
- [ ] Selecting category filters results
- [ ] "All Categories" option shows all tools
- [ ] Page resets to 1 when filtering

#### Pagination
- [ ] Pagination controls appear when total > limit
- [ ] "Previous" button disabled on first page
- [ ] "Next" button disabled on last page
- [ ] Page number displays correctly
- [ ] Clicking Previous/Next changes page
- [ ] Results update when changing pages

#### Edit Tool
- [ ] Click "Edit" button opens modal
- [ ] Modal displays with glass theme
- [ ] Form pre-fills with tool data
- [ ] All fields editable (name, vendor, category, description, status)
- [ ] Character count shows for description
- [ ] Form validation works (required fields)
- [ ] "Save Changes" submits update
- [ ] Success message appears after save
- [ ] Table refreshes with updated data
- [ ] "Cancel" closes modal without changes
- [ ] Close (×) button closes modal

#### Delete Tool
- [ ] Click "Delete" button opens confirmation dialog
- [ ] Dialog displays with warning icon
- [ ] Tool name shown in confirmation message
- [ ] Soft delete option selected by default
- [ ] Hard delete option selectable
- [ ] Warning message for hard delete appears
- [ ] "Soft Delete" button works
- [ ] "Delete Permanently" button works (hard delete)
- [ ] Success message appears after delete
- [ ] Table refreshes after delete
- [ ] "Cancel" closes dialog without action

#### Error Handling
- [ ] Network errors display error message
- [ ] Invalid token shows authentication error
- [ ] Form validation errors display
- [ ] API errors show user-friendly messages

#### Accessibility
- [ ] All buttons have proper labels
- [ ] Form inputs have labels
- [ ] Modal can be closed with Escape key
- [ ] Keyboard navigation works
- [ ] Focus management in modals

#### Visual/UI
- [ ] Glass morphism theme consistent
- [ ] Hover effects on buttons and rows
- [ ] Loading states show spinners
- [ ] Colors match design system
- [ ] Responsive layout works on mobile
- [ ] No layout shifts or flashing content

## Integration Testing

### Complete Workflow
1. Navigate to Admin page
2. Enter admin token
3. Click "Manage Tools" tab
4. Search for a tool
5. Edit the tool
6. Verify update appears immediately
7. Delete the tool (soft delete)
8. Verify tool no longer appears
9. Refresh page
10. Verify tool still deleted

### Edge Cases to Test
- Empty search results
- No tools in database
- Very long tool names/descriptions
- Special characters in search
- Rapid clicking of buttons
- Network timeouts
- Invalid admin tokens
- Concurrent edits (if multiple admins)

## Performance Testing

### Expected Metrics
- Page load: < 2s
- Search debounce: 300ms
- API response: < 500ms
- Table render: < 100ms for 20 items
- Modal open/close: < 50ms

### Load Testing
- Test with 100+ tools
- Test pagination with large datasets
- Test rapid search queries
- Monitor memory usage during long sessions

## Security Testing

### Checklist
- [ ] All endpoints require admin token
- [ ] Invalid tokens rejected with 401
- [ ] Input validation prevents injection
- [ ] Audit logs created for all actions
- [ ] Tool IDs validated (UUID format)
- [ ] SQL injection protection in queries
- [ ] XSS protection in frontend

## Browser Compatibility

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

## Automated Testing

Run unit tests:
```bash
cd backend
python tests/test_phase5.py
```

Run frontend build:
```bash
cd frontend
npm run build
```

## Known Limitations

1. Pagination in mock container doesn't respect OFFSET/LIMIT exactly
2. No real-time updates (requires manual refresh)
3. No undo/redo functionality
4. No bulk operations
5. No export functionality

## Future Enhancements

- Real-time updates via WebSockets
- Bulk tool import/export
- Tool versioning history
- Advanced filtering (multiple categories, date ranges)
- Sorting by different columns
- Tool usage analytics
