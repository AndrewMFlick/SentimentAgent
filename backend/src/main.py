"""FastAPI application."""
import logging
import asyncio
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api import router
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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Configure standard logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with proper startup and shutdown handling."""
    # Startup
    logger.info("application_startup", event="starting")
    
    try:
        # Initialize database (fail-fast on connection failure)
        logger.info("database_initialization", event="starting")
        await db.initialize()
        app_state.database_connected = True
        logger.info("database_initialization", event="completed")
        
        # Start scheduler
        logger.info("scheduler_startup", event="starting")
        scheduler.start()
        logger.info("scheduler_startup", event="completed")
        
        # Load recent data in background (non-blocking)
        logger.info("data_loading", event="starting_background_task")
        asyncio.create_task(db.load_recent_data())
        
        logger.info("application_startup", event="completed", uptime_seconds=app_state.get_uptime_seconds())
        
    except Exception as e:
        logger.critical("application_startup", event="failed", error=str(e), exc_info=True)
        app_state.database_connected = False
        raise  # Fail-fast: crash the application if startup fails
    
    yield
    
    # Shutdown
    logger.info("application_shutdown", event="starting")
    
    try:
        # Stop scheduler gracefully (wait for running jobs to complete)
        logger.info("scheduler_shutdown", event="starting")
        scheduler.stop()
        logger.info("scheduler_shutdown", event="completed")
        
        # Disconnect database
        logger.info("database_shutdown", event="starting")
        app_state.database_connected = False
        logger.info("database_shutdown", event="completed")
        
        logger.info("application_shutdown", event="completed", uptime_seconds=app_state.get_uptime_seconds())
        
    except Exception as e:
        logger.error("application_shutdown", event="error", error=str(e), exc_info=True)


# Create FastAPI app
app = FastAPI(
    title="Reddit Sentiment Analysis API",
    description="API for analyzing sentiment of AI developer tool discussions on Reddit",
    version="1.0.0",
    lifespan=lifespan
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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Reddit Sentiment Analysis API",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
