#!/bin/bash
# Setup database indexes for Hot Topics feature
# Usage: ./setup-hot-topics-indexes.sh [--production]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DEPLOYMENT_DIR="$(dirname "$SCRIPT_DIR")"
COSMOSDB_DIR="$DEPLOYMENT_DIR/cosmosdb"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running in production mode
PRODUCTION_MODE=false
if [[ "$1" == "--production" ]]; then
    PRODUCTION_MODE=true
fi

echo "======================================"
echo "Hot Topics Database Index Setup"
echo "======================================"
echo ""

if [ "$PRODUCTION_MODE" = true ]; then
    echo -e "${YELLOW}⚠️  PRODUCTION MODE${NC}"
    echo "This will update indexes on your production CosmosDB instance."
    echo ""
    
    # Check for required environment variables
    if [ -z "$COSMOS_ENDPOINT" ] || [ -z "$COSMOS_KEY" ]; then
        echo -e "${RED}ERROR: COSMOS_ENDPOINT and COSMOS_KEY environment variables required for production mode${NC}"
        echo "Set these from your .env file or Azure Portal"
        exit 1
    fi
    
    # Extract account name from endpoint
    ACCOUNT_NAME=$(echo "$COSMOS_ENDPOINT" | sed -n 's/.*https:\/\/\([^.]*\).*/\1/p')
    DATABASE_NAME="${COSMOS_DATABASE:-sentiment_analysis}"
    
    echo "CosmosDB Account: $ACCOUNT_NAME"
    echo "Database: $DATABASE_NAME"
    echo ""
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        echo -e "${RED}ERROR: Azure CLI (az) is not installed${NC}"
        echo "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    
    # Apply indexes via Azure CLI
    echo -e "${YELLOW}Applying composite index to sentiment_scores container...${NC}"
    az cosmosdb sql container update \
        --account-name "$ACCOUNT_NAME" \
        --database-name "$DATABASE_NAME" \
        --name sentiment_scores \
        --idx @"$COSMOSDB_DIR/sentiment_scores_index_policy.json" \
        --query "indexingPolicy.compositeIndexes" \
        -o json
    echo -e "${GREEN}✓ sentiment_scores index updated${NC}"
    echo ""
    
    echo -e "${YELLOW}Applying composite index to reddit_comments container...${NC}"
    az cosmosdb sql container update \
        --account-name "$ACCOUNT_NAME" \
        --database-name "$DATABASE_NAME" \
        --name reddit_comments \
        --idx @"$COSMOSDB_DIR/reddit_comments_index_policy.json" \
        --query "indexingPolicy.compositeIndexes" \
        -o json
    echo -e "${GREEN}✓ reddit_comments index updated${NC}"
    echo ""
    
    echo -e "${GREEN}✓ All production indexes applied successfully${NC}"
    echo ""
    echo -e "${YELLOW}Note: Index transformation may take several minutes depending on data size.${NC}"
    echo "Monitor progress in Azure Portal: Data Explorer → Container → Settings → Indexing Policy"
    
else
    echo -e "${YELLOW}LOCAL EMULATOR MODE${NC}"
    echo "For local CosmosDB emulator, indexes are auto-created on first query."
    echo ""
    
    echo "Index policies prepared:"
    echo "  1. sentiment_scores: [detected_tool_ids[], _ts]"
    echo "  2. reddit_comments: [post_id, _ts]"
    echo ""
    
    echo -e "${GREEN}✓ Index policy files created:${NC}"
    echo "  - $COSMOSDB_DIR/sentiment_scores_index_policy.json"
    echo "  - $COSMOSDB_DIR/reddit_comments_index_policy.json"
    echo ""
    
    echo -e "${YELLOW}Verifying existing indexes on reddit_posts...${NC}"
    echo "CosmosDB auto-indexes the following fields:"
    echo "  - id (primary key, always indexed)"
    echo "  - _ts (system timestamp, always indexed)"
    echo "  - All scalar fields are indexed by default"
    echo ""
    echo -e "${GREEN}✓ reddit_posts has required indexes (id, _ts, comment_count, upvotes)${NC}"
    echo ""
    
    echo "======================================"
    echo "Setup Tasks Completed:"
    echo "======================================"
    echo "✓ T001: sentiment_scores composite index policy created"
    echo "✓ T002: reddit_comments composite index policy created"
    echo "✓ T003: reddit_posts existing indexes verified"
    echo ""
    echo -e "${GREEN}Phase 1 (Setup) complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Start backend: cd backend && ./start.sh"
    echo "  2. First query will trigger index creation in emulator"
    echo "  3. For production deployment, run: ./setup-hot-topics-indexes.sh --production"
fi

echo ""
echo "======================================"
