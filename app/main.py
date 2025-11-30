"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import upload, products, webhooks, sse
from app.config import settings
import os

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Product Importer API",
    description="API for importing and managing products from CSV files",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint (define before static files)
@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Include routers
app.include_router(upload.router)
app.include_router(products.router)
app.include_router(webhooks.router)
app.include_router(sse.router)

# Mount static files (must be last to not interfere with API routes)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    # Only mount root if we want to serve index.html, but API routes take precedence
    # We'll mount it but FastAPI should check routes first
    try:
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="root")
    except Exception:
        # If static files fail, continue without them
        pass

