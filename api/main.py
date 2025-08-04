#!/usr/bin/env python3
"""
FPAS FastAPI Application
Production-grade API for Finnish Politician Analysis System
"""

import sys
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

# Add project root to path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="Finnish Politician Analysis System API",
        description="""
        The Finnish Politician Analysis System provides analysis and insights
        about Finnish politicians based on news, public statements, and voting records.
        
        ## Features
        
        * **Politicians**: Retrieve politician data and profiles
        * **News Analysis**: Analyze sentiment and topics in politician media coverage
        * **Relationship Analysis**: Explore political networks and connections
        * **AI Insights**: Generate AI-powered analysis of political trends
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Setup CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For production, restrict to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routes
    from api.routers import politicians, news, analysis, health, provinces
    from api.core.config import Settings
    settings = Settings()
    
    app.include_router(health.router, prefix=settings.API_V1_STR)
    app.include_router(politicians.router, prefix=settings.API_V1_STR)
    app.include_router(news.router, prefix=settings.API_V1_STR)
    app.include_router(analysis.router, prefix=settings.API_V1_STR)
    app.include_router(provinces.router, prefix=settings.API_V1_STR)
    
    return app

app = create_app()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title="Finnish Politician Analysis System API",
        version="1.0.0",
        description="API for analyzing Finnish politicians and their relationships",
        routes=app.routes,
    )
    
    # Custom documentation enhancements
    openapi_schema["info"]["x-logo"] = {
        "url": "https://finland.fi/wp-content/uploads/2017/01/finland_coat_of_arms.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/", tags=["root"])
async def root():
    """Root endpoint providing API information"""
    return {
        "name": "Finnish Politician Analysis System API",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
