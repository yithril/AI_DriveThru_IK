"""
FastAPI application main entry point
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dependency_injector.wiring import Provide, inject

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from app.core.container import Container
from app.api.ingredients_controller import router as ingredients_router
from app.api.categories_controller import router as categories_router
from app.api.menu_items_controller import router as menu_items_router
from app.api.file_upload_controller import router as file_upload_router
from app.api.restaurants_controller import router as restaurants_router
from app.api.customer_controller import router as customer_router
from app.api.voice_controller import router as voice_router
from app.api.sessions_controller import router as sessions_router
from app.api.orders_controller import router as orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting application startup")
    try:
        from app.core.database import init_database, close_database
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database during startup: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Starting application shutdown")
    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Create FastAPI app
app = FastAPI(
    title="AI DriveThru API",
    description="API for AI-powered drive-thru restaurant management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(restaurants_router)
app.include_router(customer_router)
app.include_router(ingredients_router)
app.include_router(categories_router)
app.include_router(menu_items_router)
app.include_router(file_upload_router)
app.include_router(voice_router)
app.include_router(sessions_router)
app.include_router(orders_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI DriveThru API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Initialize container and wire dependencies
logger.info("Initializing dependency injection container")
container = Container()

# Wire the container to the routers
logger.info("Wiring dependency injection to routers")
container.wire(modules=[
    "app.api.restaurants_controller",
    "app.api.customer_controller",
    "app.api.ingredients_controller",
    "app.api.categories_controller",
    "app.api.menu_items_controller", 
    "app.api.file_upload_controller",
    "app.api.voice_controller",
    "app.api.sessions_controller",
    "app.api.orders_controller"
])

# Make container available to the app
app.container = container
logger.info("Application setup completed successfully")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
