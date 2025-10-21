"""Sentiment aggregation service for daily time period computation."""
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class SentimentAggregator:
    """Compute daily sentiment aggregates for AI tools."""
    
    def __init__(self, database_service):
        """
        Initialize sentiment aggregator.
        
        Args:
            database_service: Database service instance
        """
        self.db = database_service
    
    async def compute_daily_aggregates(
        self,
        date: str | None = None
    ) -> list[dict]:
        """
        Compute sentiment aggregates for all tools for a date.
        
        Args:
            date: Date in YYYY-MM-DD format (default: yesterday)
            
        Returns:
            List of computed aggregates
        """
        if date is None:
            # Default to yesterday
            yesterday = datetime.utcnow() - timedelta(days=1)
            date = yesterday.strftime("%Y-%m-%d")
        
        logger.info(
            "Computing daily sentiment aggregates",
            date=date
        )
        
        # Get all approved tools
        tools = await self.db.get_approved_tools()
        
        aggregates = []
        for tool in tools:
            aggregate = await self.compute_aggregate_for_date(
                tool["id"],
                date
            )
            if aggregate:
                aggregates.append(aggregate)
        
        logger.info(
            "Daily aggregates computed",
            date=date,
            tool_count=len(aggregates)
        )
        
        return aggregates
    
    async def compute_aggregate_for_date(
        self,
        tool_id: str,
        date: str
    ) -> dict | None:
        """
        Compute aggregate for single tool and date.
        
        Args:
            tool_id: Tool identifier
            date: Date in YYYY-MM-DD format
            
        Returns:
            Aggregate record or None if no data
        """
        # Query tool mentions for the date
        query = """
            SELECT
                tm.tool_id,
                COUNT(1) as total_mentions,
                SUM(CASE WHEN ss.sentiment = 'positive'
                    THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN ss.sentiment = 'negative'
                    THEN 1 ELSE 0 END) as negative_count,
                SUM(CASE WHEN ss.sentiment = 'neutral'
                    THEN 1 ELSE 0 END) as neutral_count,
                AVG(ss.compound_score) as avg_sentiment
            FROM tool_mentions tm
            JOIN sentiment_scores ss ON tm.content_id = ss.content_id
            WHERE tm.tool_id = @tool_id
                AND SUBSTRING(tm.detected_at, 0, 10) = @date
            GROUP BY tm.tool_id
        """
        
        results = await self.db.query_items(
            "tool_mentions",
            query,
            parameters=[
                {"name": "@tool_id", "value": tool_id},
                {"name": "@date", "value": date}
            ]
        )
        
        if not results:
            return None
        
        data = results[0]
        
        # Create aggregate record
        aggregate = {
            "id": f"{tool_id}_{date}",
            "tool_id": tool_id,
            "date": date,
            "total_mentions": data.get("total_mentions", 0),
            "positive_count": data.get("positive_count", 0),
            "negative_count": data.get("negative_count", 0),
            "neutral_count": data.get("neutral_count", 0),
            "avg_sentiment": data.get("avg_sentiment", 0.0),
            "computed_at": datetime.utcnow().isoformat(),
            "deleted_at": None
        }
        
        # Upsert to database
        await self.db.upsert_item("time_period_aggregates", aggregate)
        
        logger.debug(
            "Computed aggregate for tool",
            tool_id=tool_id,
            date=date,
            mentions=aggregate["total_mentions"]
        )
        
        return aggregate


# Global instance (initialized later with db)
sentiment_aggregator: SentimentAggregator | None = None
