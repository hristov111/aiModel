"""FastAPI application initialization."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import init_db, close_db, engine
from app.utils.embeddings import get_embedding_generator
from app.utils.rate_limiter import limiter
from app.api.routes import router
from app.core.exceptions import AICompanionException
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.metrics import PrometheusMiddleware, get_metrics, get_metrics_content_type

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting AI Companion Service...")
    
    try:
        # Initialize database connection
        logger.info("Initializing database connection...")
        # Database will be connected on first request
        
        # Pre-load embedding model
        logger.info("Loading embedding model...")
        embedding_generator = get_embedding_generator()
        logger.info(f"Embedding model loaded: {embedding_generator.dimension} dimensions")
        
        logger.info("AI Companion Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Companion Service...")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Create FastAPI app
app = FastAPI(
    title="AI Companion Service",
    description="A standalone microservice for conversational AI with memory",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware for tracing
app.add_middleware(RequestIDMiddleware)

# Add Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Exception handlers
@app.exception_handler(AICompanionException)
async def ai_companion_exception_handler(request: Request, exc: AICompanionException):
    """Handle custom AI Companion exceptions."""
    logger.error(f"AI Companion error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.__class__.__name__,
            "detail": str(exc)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(router, prefix="", tags=["chat"])


# Mount static files for frontend
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
    logger.info(f"Mounted frontend static files from {frontend_dir}")
    
    # Serve chat.html at /chat
    from fastapi.responses import FileResponse
    
    @app.get("/chat")
    async def serve_chat():
        """Serve the chat frontend interface."""
        return FileResponse(str(frontend_dir / "chat.html"))
else:
    logger.warning(f"Frontend directory not found at {frontend_dir}")


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Exposes application metrics in Prometheus format for monitoring.
    """
    from fastapi.responses import Response
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=settings.log_level.lower()
    )

