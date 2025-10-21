"""FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .api.admin import router as admin_router
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

        from .services.sentiment_aggregator import SentimentAggregator
        from .services.tool_manager import ToolManager

        tool_manager_instance = ToolManager(db)
        sentiment_aggregator_instance = SentimentAggregator(db)

        # Update module globals
        sys.modules["src.services.tool_manager"].tool_manager = tool_manager_instance
        sys.modules["src.services.sentiment_aggregator"].sentiment_aggregator = (
            sentiment_aggregator_instance
        )

        logger.info("AI Tools services initialized")

        # Start scheduler
        logger.info("Starting scheduler")
        scheduler.start()
        logger.info("Scheduler started successfully")

        # Load recent data in background (non-blocking)
        logger.info("Starting background data loading task")
        asyncio.create_task(db.load_recent_data())

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
