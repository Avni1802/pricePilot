from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import logging
from datetime import datetime
from typing import List

from app.models.product import (
    ProductQuery, 
    ProductResult, 
    SearchResponse, 
    HealthResponse
)
from app.services.serpapi_client import SerpAPIClient
from app.services.openai_client import OpenAIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for services
serpapi_client = None
openai_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    global serpapi_client, openai_client
    
    logger.info("Starting PricePilot API...")
    
    try:
        # Initialize SerpAPI client
        serpapi_client = SerpAPIClient()
        logger.info("SerpAPI client initialized")
        
        # Initialize OpenAI client
        openai_client = OpenAIClient()
        logger.info("OpenAI client initialized")
        
        # Test connections
        serpapi_status = await serpapi_client.test_connection()
        openai_status = await openai_client.test_connection()
        
        logger.info(f"SerpAPI connection: {'✓' if serpapi_status['connected'] else '✗'}")
        logger.info(f"OpenAI connection: {'✓' if openai_status['connected'] else '✗'}")
        
        logger.info("PricePilot API startup complete!")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise e
    
    yield
    
    # Shutdown
    logger.info("PricePilot API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="PricePilot API",
    description="Universal product price comparison tool with AI-powered matching",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_serpapi_client() -> SerpAPIClient:
    """Dependency to get SerpAPI client"""
    if serpapi_client is None:
        raise HTTPException(status_code=500, detail="SerpAPI client not initialized")
    return serpapi_client

def get_openai_client() -> OpenAIClient:
    """Dependency to get OpenAI client"""
    if openai_client is None:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized")
    return openai_client

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to PricePilot API",
        "description": "Universal product price comparison tool",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "docs": "/docs",
            "test_services": "/test-services"
        },
        "example_usage": {
            "endpoint": "/search",
            "method": "POST",
            "body": {
                "country": "US",
                "query": "iPhone 16 Pro, 128GB"
            }
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test service connections
        services_status = {}
        
        if serpapi_client:
            serpapi_status = await serpapi_client.test_connection()
            services_status["serpapi"] = serpapi_status["connected"]
        
        if openai_client:
            openai_status = await openai_client.test_connection()
            services_status["openai"] = openai_status["connected"]
        
        return HealthResponse(
            status="ok",
            message="PricePilot API is running",
            timestamp=datetime.now().isoformat(),
            services=services_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def search_products(
    query: ProductQuery,
    serpapi: SerpAPIClient = Depends(get_serpapi_client),
    openai: OpenAIClient = Depends(get_openai_client)
):
    """Search for products across multiple sources"""
    start_time = time.time()
    
    try:
        logger.info(f"Starting search for: '{query.query}' in {query.country}")
        
        # For Phase 1, we'll just return a basic response structure
        # The actual search logic will be implemented in Phase 2
        
        # Placeholder: Test SerpAPI connection
        serpapi_test = await serpapi.test_connection()
        if not serpapi_test["connected"]:
            raise HTTPException(status_code=500, detail="SerpAPI connection failed")
        
        # Placeholder results for Phase 1
        results = []
        
        search_time = time.time() - start_time
        
        logger.info(f"Search completed in {search_time:.2f} seconds")
        
        return SearchResponse(
            success=True,
            message=f"Search infrastructure ready for '{query.query}' in {query.country}",
            results=results,
            total_results=len(results),
            search_time_seconds=round(search_time, 2),
            country=query.country,
            query=query.query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/test-services")
async def test_all_services(
    serpapi: SerpAPIClient = Depends(get_serpapi_client),
    openai: OpenAIClient = Depends(get_openai_client)
):
    """Test all external service connections"""
    try:
        # Test SerpAPI
        serpapi_status = await serpapi.test_connection()
        
        # Test OpenAI
        openai_status = await openai.test_connection()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "services": {
                "serpapi": serpapi_status,
                "openai": openai_status
            },
            "overall_status": "ok" if serpapi_status["connected"] and openai_status["connected"] else "degraded"
        }
        
    except Exception as e:
        logger.error(f"Service test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service test failed: {str(e)}")

# Additional utility endpoints for debugging
@app.get("/countries")
async def get_supported_countries():
    """Get list of supported countries"""
    from app.models.product import CountryCode
    return {
        "supported_countries": [country.value for country in CountryCode],
        "total_count": len(CountryCode)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")