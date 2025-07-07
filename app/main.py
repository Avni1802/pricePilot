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
    HealthResponse,
)
from app.services.serpapi_client import SerpAPIClient
from app.services.openai_client import OpenAIClient
from app.services.data_parser import ProductDataParser

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables for services
serpapi_client = None
openai_client = None
data_parser = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    global serpapi_client, openai_client, data_parser

    logger.info("Starting PricePilot API...")

    try:
        # Initialize services
        serpapi_client = SerpAPIClient()
        logger.info("SerpAPI client initialized")

        # Initialize OpenAI client
        openai_client = OpenAIClient()
        logger.info("OpenAI client initialized")
        data_parser = ProductDataParser()  # Add parser initialization

        logger.info("All services initialized successfully")

        # Test connections
        serpapi_status = await serpapi_client.test_connection()
        openai_status = await openai_client.test_connection()

        logger.info(
            f"SerpAPI connection: {'✓' if serpapi_status['connected'] else '✗'}"
        )
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
    redoc_url="/redoc",
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


def get_data_parser() -> ProductDataParser:
    """Dependency to get data parser"""
    if data_parser is None:
        raise HTTPException(status_code=500, detail="Data parser not initialized")
    return data_parser


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to PricePilot API - Phase 2",
        "description": "Universal product price comparison tool with real search",
        "version": "1.0.0",
        "phase": "2 - Core Search Implementation",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "docs": "/docs",
            "test_services": "/test-services",
        },
        "example_usage": {
            "endpoint": "/search",
            "method": "POST",
            "body": {"country": "US", "query": "iPhone 16 Pro, 128GB"},
        },
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

        # Add parser status
        services_status["data_parser"] = data_parser is not None

        return HealthResponse(
            status="ok",
            message="PricePilot API is running - Phase 2",
            timestamp=datetime.now().isoformat(),
            services=services_status,
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_products(
    query: ProductQuery,
    serpapi: SerpAPIClient = Depends(get_serpapi_client),
    openai: OpenAIClient = Depends(get_openai_client),
    parser: ProductDataParser = Depends(get_data_parser),
):
    """
    Search for products across multiple worldwide sources

    What this does: Orchestrates search across Google Shopping, Amazon, eBay, and local sites
    Why: Provides comprehensive price comparison from global sources
    Returns: List of products with prices from multiple websites
    """
    start_time = time.time()

    try:
        logger.info(
            f"Starting comprehensive search for: '{query.query}' in {query.country}"
        )

        # Step 1: Execute searches across all sources
        logger.info("Executing multi-source search...")
        raw_results = await serpapi.search_all_sources(query.query, query.country)

        # Step 2: Parse raw results into structured data
        logger.info("🔧 Parsing raw results...")
        parsed_products = parser.parse_all_results(raw_results, query.country)

        # Step 3: Convert to ProductResult format
        logger.info("📦 Converting to final format...")
        final_results = []

        for product_data in parsed_products:
            try:
                # Create ProductResult object to ensure validation
                product_result = ProductResult(**product_data)
                final_results.append(product_result.dict())
            except Exception as e:
                logger.warning(f"Skipping invalid product: {str(e)}")
                continue

        # Step 4: Sort by price (lowest first)
        logger.info("💰 Sorting by price...")
        final_results.sort(key=lambda x: float(x.get("price", "999999")))

        search_time = time.time() - start_time

        logger.info(
            f"Search completed! Found {len(final_results)} products in {search_time:.2f}s"
        )

        return SearchResponse(
            success=True,
            message=f"Found {len(final_results)} products for '{query.query}' in {query.country}",
            results=final_results,
            total_results=len(final_results),
            search_time_seconds=round(search_time, 2),
            country=query.country,
            query=query.query,
        )

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/test-services")
async def test_all_services(
    serpapi: SerpAPIClient = Depends(get_serpapi_client),
    openai: OpenAIClient = Depends(get_openai_client),
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
                "openai": openai_status,
                "data_parser": {
                    "connected": data_parser is not None,
                    "message": "Data parser initialized",
                },
            },
            "overall_status": (
                "ok"
                if serpapi_status["connected"] and openai_status["connected"]
                else "degraded"
            ),
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
        "total_count": len(CountryCode),
    }


# Debug endpoint for raw search results
@app.post("/debug-search")
async def debug_search(
    query: ProductQuery, serpapi: SerpAPIClient = Depends(get_serpapi_client)
):
    """Debug endpoint to see raw search results"""
    try:
        logger.info(f"Debug search for: {query.query} in {query.country}")
        raw_results = await serpapi.search_all_sources(query.query, query.country)

        return {
            "query": query.query,
            "country": query.country,
            "raw_results": raw_results,
            "sources_found": list(raw_results.keys()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
