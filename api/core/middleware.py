"""
Middleware components for FPAS API
Provides error handling, request logging, and other middleware
"""

import time
import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from neo4j.exceptions import ServiceUnavailable, AuthError
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fpas_api")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and response times"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log the exception
            logger.error(f"Request error: {str(e)}")
            raise
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log the request details and processing time
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Process time: {process_time:.4f}s"
        )
        
        # Add processing time header to the response
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

async def neo4j_exception_handler(request: Request, exc: ServiceUnavailable):
    """Handle Neo4j service unavailable exceptions"""
    logger.error(f"Neo4j service unavailable: {str(exc)}")
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database service unavailable, please try again later",
            "error": "neo4j_unavailable"
        }
    )

async def neo4j_auth_exception_handler(request: Request, exc: AuthError):
    """Handle Neo4j authentication errors"""
    logger.error(f"Neo4j authentication error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Database authentication error",
            "error": "neo4j_auth_error"
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for all unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "error": "internal_server_error",
            "message": str(exc)
        }
    )

def setup_middleware(app: FastAPI):
    """Configure all middleware for the FastAPI application"""
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add exception handlers
    app.add_exception_handler(ServiceUnavailable, neo4j_exception_handler)
    app.add_exception_handler(AuthError, neo4j_auth_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
