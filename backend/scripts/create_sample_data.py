#!/usr/bin/env python3
"""Create sample tool mentions and aggregates for Feature #008 testing."""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.cosmos.aio import CosmosClient
from src.config import settings
import structlog

logger = structlog.get_logger()


async def create_sample_data():
    """Create sample tool mentions and time period aggregates."""
    logger.info("Starting sample data creation for Feature #008")
    
    async with CosmosClient(
        settings.cosmos_endpoint,
        credential=settings.cosmos_key
    ) as client:
        database = client.get_database_client(settings.cosmos_database)
        
        # Get containers
        mentions_container = database.get_container_client("tool_mentions")
        aggregates_container = database.get_container_client("time_period_aggregates")
        
        # Sample tool mentions for GitHub Copilot and Jules AI
        today = datetime.utcnow()
        mentions = []
        
        # GitHub Copilot mentions (last 7 days)
        for i in range(20):
            mention_date = today - timedelta(days=(i % 7), hours=i)
            mentions.append({
                "id": f"mention-copilot-{i}",
                "tool_id": "github-copilot",
                "content_id": f"sample-post-{i}",
                "content_type": "post" if i % 2 == 0 else "comment",
                "subreddit": ["programming", "github", "vscode"][i % 3],
                "mention_text": f"GitHub Copilot sample mention {i}",
                "confidence": 0.85 + (i % 10) * 0.01,
                "detected_at": mention_date.isoformat(),
                "sentiment_score_id": None
            })
        
        # Jules AI mentions (last 7 days)
        for i in range(15):
            mention_date = today - timedelta(days=(i % 7), hours=i + 5)
            mentions.append({
                "id": f"mention-jules-{i}",
                "tool_id": "jules-ai",
                "content_id": f"sample-post-jules-{i}",
                "content_type": "post" if i % 2 == 0 else "comment",
                "subreddit": ["programming", "ai", "machinelearning"][i % 3],
                "mention_text": f"Jules AI sample mention {i}",
                "confidence": 0.80 + (i % 15) * 0.01,
                "detected_at": mention_date.isoformat(),
                "sentiment_score_id": None
            })
        
        # Insert mentions
        for mention in mentions:
            try:
                await mentions_container.upsert_item(mention)
                logger.info(
                    "Created mention",
                    mention_id=mention["id"],
                    tool_id=mention["tool_id"]
                )
            except Exception as e:
                logger.error(f"Failed to create mention {mention['id']}: {e}")
        
        logger.info(f"✅ Created {len(mentions)} tool mentions")
        
        # Create time period aggregates (last 30 days)
        aggregates = []
        
        for days_ago in range(30):
            date = (today - timedelta(days=days_ago)).date().isoformat()
            
            # GitHub Copilot aggregate
            # Simulate varying sentiment over time
            base_positive = 60 + (days_ago % 20)
            base_negative = 20 + (days_ago % 10)
            base_neutral = 30 - (days_ago % 15)
            
            aggregates.append({
                "id": f"github-copilot-{date}",
                "tool_id": "github-copilot",
                "date": date,
                "total_mentions": base_positive + base_negative + base_neutral,
                "positive_count": base_positive,
                "negative_count": base_negative,
                "neutral_count": base_neutral,
                "avg_sentiment": 0.25 + (days_ago % 20) * 0.02,
                "computed_at": datetime.utcnow().isoformat(),
                "deleted_at": None
            })
            
            # Jules AI aggregate
            jules_positive = 40 + (days_ago % 15)
            jules_negative = 15 + (days_ago % 8)
            jules_neutral = 20 - (days_ago % 10)
            
            aggregates.append({
                "id": f"jules-ai-{date}",
                "tool_id": "jules-ai",
                "date": date,
                "total_mentions": jules_positive + jules_negative + jules_neutral,
                "positive_count": jules_positive,
                "negative_count": jules_negative,
                "neutral_count": jules_neutral,
                "avg_sentiment": 0.30 + (days_ago % 15) * 0.03,
                "computed_at": datetime.utcnow().isoformat(),
                "deleted_at": None
            })
        
        # Insert aggregates
        for aggregate in aggregates:
            try:
                await aggregates_container.upsert_item(aggregate)
                logger.info(
                    "Created aggregate",
                    aggregate_id=aggregate["id"],
                    date=aggregate["date"]
                )
            except Exception as e:
                logger.error(f"Failed to create aggregate {aggregate['id']}: {e}")
        
        logger.info(f"✅ Created {len(aggregates)} time period aggregates")
        logger.info("Sample data creation complete!")
        logger.info("You can now test Feature #008 endpoints:")
        logger.info("  - GET /api/v1/tools")
        logger.info("  - GET /api/v1/tools/github-copilot/sentiment")
        logger.info("  - GET /api/v1/tools/jules-ai/sentiment")
        logger.info("  - GET /api/v1/tools/compare?tool_ids=github-copilot,jules-ai")
        logger.info("  - GET /api/v1/tools/github-copilot/timeseries?start_date=...&end_date=...")


if __name__ == "__main__":
    asyncio.run(create_sample_data())
