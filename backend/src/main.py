"""FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .api.admin import router as admin_router
from .api.hot_topics import router as hot_topics_router
from .config import settings
from .services import db, scheduler
from .services.health import app_state

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Configure standard logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = structlog.get_logger(__name__)


async def _register_tools_with_detector(database):
    """Register all active tools with the tool detector for sentiment analysis."""
    from .services.tool_detector import tool_detector

    try:
        # Get all active tools from the database
        tools_container = database.database.get_container_client("Tools")
        query = "SELECT * FROM c WHERE c.status = 'active' AND c.partitionKey = 'tool'"

        tools = list(
            tools_container.query_items(query=query, enable_cross_partition_query=False)
        )

        # Register each tool with its aliases
        for tool in tools:
            tool_id = tool["id"]
            name = tool["name"]
            aliases = [name.lower()]  # Start with tool name

            # Add slug as alias
            if "slug" in tool:
                aliases.append(tool["slug"].lower())

            # TODO: When ToolAliases container is populated, load aliases from there
            # For now, use common variations of the tool name
            # e.g., "GitHub Copilot" -> ["github copilot", "copilot", "gh copilot"]
            if " " in name:
                parts = name.lower().split()
                if len(parts) > 1:
                    aliases.append(parts[-1])  # Last word (e.g., "Copilot")

            tool_detector.register_tool(
                tool_id=tool_id,
                aliases=aliases,
                threshold=0.5,  # Lower threshold for better recall
            )

        logger.info("Tools registered with detector", tool_count=len(tools))

    except Exception as e:
        logger.error(
            "Failed to register tools with detector", error=str(e), exc_info=True
        )
        # Don't fail startup if tool registration fails


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with proper startup and shutdown handling."""
    # Startup
    logger.info("Application startup beginning")

    try:
        # Initialize database (fail-fast on connection failure)
        logger.info("Initializing database connection")
        await db.initialize()
        app_state.database_connected = True
        logger.info("Database initialization completed")

        # Initialize AI Tools services
        logger.info("Initializing AI Tools services")
        # Create global instances
        import sys

        from .services.cache_service import CacheService
        from .services.sentiment_aggregator import SentimentAggregator
        from .services.tool_manager import ToolManager

        tool_manager_instance = ToolManager(db)
        sentiment_aggregator_instance = SentimentAggregator(db)

        # Update module globals
        sys.modules["src.services.tool_manager"].tool_manager = (
            tool_manager_instance
        )
        sys.modules["src.services.sentiment_aggregator"].sentiment_aggregator = (
            sentiment_aggregator_instance
        )

        # Initialize cache service (Feature 017)
        if settings.enable_sentiment_cache:
            logger.info("Initializing sentiment cache service")
            cache_container = db.database.get_container_client(
                settings.cosmos_container_sentiment_cache
            )
            sentiment_container = db.database.get_container_client(
                settings.cosmos_container_sentiment
            )
            tools_container = db.database.get_container_client("Tools")

            cache_service_instance = CacheService(
                cache_container=cache_container,
                sentiment_container=sentiment_container,
                tools_container=tools_container,
            )

            # Update module global
            sys.modules["src.services.cache_service"].cache_service = (
                cache_service_instance
            )
            logger.info("Sentiment cache service initialized")
        else:
            logger.info(
                "Sentiment cache disabled",
                enable_sentiment_cache=settings.enable_sentiment_cache,
            )

        # Register tools with the detector for sentiment analysis
        logger.info("Registering tools with detector")
        await _register_tools_with_detector(db)

        logger.info("AI Tools services initialized")

        # Start scheduler
        logger.info("Starting scheduler")
        scheduler.start()
        logger.info("Scheduler started successfully")

        # Load recent data in background (non-blocking)
        logger.info("Starting background data loading task")
        asyncio.create_task(db.load_recent_data())

        # Trigger initial cache population (non-blocking) - Feature 017 Phase 4
        if settings.enable_sentiment_cache:
            logger.info("Triggering initial cache population")
            from .services.cache_service import cache_service
            if cache_service:
                asyncio.create_task(cache_service.refresh_all_tools())
                logger.info("Initial cache population task started")

        logger.info(
            "Application startup completed",
            uptime_seconds=app_state.get_uptime_seconds(),
        )

    except Exception as e:
        logger.critical("Application startup failed", error=str(e), exc_info=True)
        app_state.database_connected = False
        raise  # Fail-fast: crash the application if startup fails

    yield

    # Shutdown
    logger.info("Application shutdown beginning")

    try:
        # Stop scheduler gracefully (wait for running jobs to complete)
        logger.info("Stopping scheduler")
        scheduler.stop()
        logger.info("Scheduler stopped")

        # Disconnect database
        logger.info("Disconnecting database")
        app_state.database_connected = False
        logger.info("Database disconnected")

        logger.info(
            "Application shutdown completed",
            uptime_seconds=app_state.get_uptime_seconds(),
        )

    except Exception as e:
        logger.error("Application shutdown error", error=str(e), exc_info=True)


# Create FastAPI app
app = FastAPI(
    title="Reddit Sentiment Analysis API",
    description="API for analyzing sentiment of AI developer tool discussions on Reddit",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "hot-topics",
            "description": "Hot Topics endpoints for viewing trending developer tools "
            "with engagement metrics and related Reddit posts. "
            "Features include time-range filtering (24h/7d/30d), "
            "engagement scoring, and sentiment distribution analysis.",
        },
        {
            "name": "admin",
            "description": "Admin endpoints for managing tools, aliases, and merges. "
            "Requires X-Admin-Token authentication.",
        },
        {
            "name": "sentiment",
            "description": "Sentiment analysis endpoints for viewing aggregated sentiment "
            "data and time series for developer tools.",
        },
    ],
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Include admin routes (requires authentication)
app.include_router(admin_router, prefix="/api/v1")

# Include hot topics routes
app.include_router(hot_topics_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Reddit Sentiment Analysis API",
        "version": "1.0.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app", host=settings.api_host, port=settings.api_port, reload=True
    )
