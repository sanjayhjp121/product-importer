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

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Serve index.html for root and non-API routes
    from fastapi.responses import FileResponse
    from fastapi import Request
    from fastapi.responses import Response
    
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        """Serve frontend for non-API routes."""
        # Don't serve frontend for API routes
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
            return Response(status_code=404)
        
        # Serve index.html for all other routes (SPA routing)
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return Response(status_code=404)

