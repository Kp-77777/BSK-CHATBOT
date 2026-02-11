"""
BSK Chatbot FastAPI backend.
Run: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from utils.logger import get_logger

from api.routers import health, chat, documents, services, logs

logger = get_logger(__name__)

app = FastAPI(
    title="BSK Chatbot API",
    description="API for document ingestion, chat, services, and logs",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Startup and Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("=" * 70)
    logger.info("FastAPI Startup - Initializing BSK Assistant Services")
    logger.info("=" * 70)
    
    try:
        # Initialize core services
        from core.vector_store import vector_store_manager
        from core.initialization import ServiceInitializer
        
        logger.info("\n[1/2] Checking core services...")
        results, critical_passed = ServiceInitializer.run_all_checks(exit_on_failure=False)
        
        logger.info("\n[2/2] Initializing vector store...")
        if vector_store_manager.is_available():
            logger.info("✓ Chroma vector store is ready")
        else:
            logger.warning("⚠ Chroma vector store may not be fully initialized")
        
        logger.info("=" * 70)
        logger.info("✓ FastAPI startup complete")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup and persist data on shutdown."""
    logger.info("=" * 70)
    logger.info("FastAPI Shutdown - Cleaning up")
    logger.info("=" * 70)
    
    try:
        # Persist Chroma to disk
        from core.vector_store import vector_store_manager
        logger.info("Persisting Chroma vector store...")
        vector_store_manager.persist()
        logger.info("✓ Chroma persisted to disk")
        
    except Exception as e:
        logger.warning(f"Error during shutdown: {e}")

API_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)
app.include_router(services.router, prefix=API_PREFIX)
app.include_router(logs.router, prefix=API_PREFIX)


@app.get("/", include_in_schema=False)
def root_health():
    """Root health check (no prefix)."""
    return {"message": "BSK Chatbot API is running", "version": "1.0.0", "status": "healthy"}


# Mount sample UI static files if directory exists
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
