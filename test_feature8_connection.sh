#!/bin/bash
# Test Feature #008 API endpoints to verify connection

echo "🔍 Testing Feature #008 API Connection"
echo "========================================"
echo ""

# Backend URL
BACKEND_URL="http://localhost:8000"

# Test 1: Health check
echo "1. Testing backend health..."
curl -s "${BACKEND_URL}/api/v1/health" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Backend is running"
else
    echo "   ❌ Backend is NOT running"
    echo "   → Start with: cd backend && ./start.sh"
    exit 1
fi
echo ""

# Test 2: Tools endpoint
echo "2. Testing /api/v1/tools endpoint..."
TOOLS_RESPONSE=$(curl -s "${BACKEND_URL}/api/v1/tools")
TOOLS_COUNT=$(echo "$TOOLS_RESPONSE" | grep -o '"id"' | wc -l | tr -d ' ')

if [ "$TOOLS_COUNT" -gt 0 ]; then
    echo "   ✅ Tools endpoint working - found $TOOLS_COUNT tools"
    echo "$TOOLS_RESPONSE" | python3 -m json.tool 2>/dev/null | head -20
else
    echo "   ⚠️  Tools endpoint working but NO TOOLS FOUND"
    echo "   → Run: cd backend && python3 scripts/seed_tools.py"
fi
echo ""

# Test 3: Admin endpoint
echo "3. Testing /api/v1/admin/tools/pending endpoint..."
curl -s "${BACKEND_URL}/api/v1/admin/tools/pending" \
    -H "X-Admin-Token: admin" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Admin endpoint accessible"
else
    echo "   ⚠️  Admin endpoint may not be accessible"
fi
echo ""

# Test 4: Frontend connectivity
echo "4. Testing frontend connectivity..."
if lsof -i :5173 > /dev/null 2>&1; then
    echo "   ✅ Frontend dev server is running on http://localhost:5173"
else
    echo "   ⚠️  Frontend dev server is NOT running"
    echo "   → Start with: cd frontend && npm run dev"
fi
echo ""

echo "========================================"
echo "📊 Summary:"
echo ""
if [ "$TOOLS_COUNT" -gt 0 ]; then
    echo "✅ Feature #008 is CONNECTED and WORKING!"
    echo ""
    echo "Next steps:"
    echo "  1. Open http://localhost:5173 in your browser"
    echo "  2. You should see AI Tools sentiment cards on the dashboard"
    echo "  3. Try the Admin page at http://localhost:5173/admin"
else
    echo "⚠️  Feature #008 is connected but needs data:"
    echo ""
    echo "Run this to add initial tools:"
    echo "  cd backend && python3 scripts/seed_tools.py"
    echo ""
    echo "Then refresh the frontend to see the tools appear!"
fi
echo ""
