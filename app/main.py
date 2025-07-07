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
from app.services.error_handler import SearchErrorHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables for services
serpapi_client = None
openai_client = None
data_parser = None
error_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global serpapi_client, openai_client, data_parser, error_handler

    logger.info("Starting PricePilot API - Phase 2...")

    try:
        # Initialize all services
        serpapi_client = SerpAPIClient()
        openai_client = OpenAIClient()
        data_parser = ProductDataParser()
        error_handler = SearchErrorHandler()

        logger.info("All services initialized successfully")

        # Test connections
        serpapi_status = await serpapi_client.test_connection()
        openai_status = await openai_client.test_connection()

        logger.info(f"SerpAPI: {'✓' if serpapi_status['connected'] else '✗'}")
        logger.info(f"OpenAI: {'✓' if openai_status['connected'] else '✗'}")
        logger.info(f"Data Parser: ✓")
        logger.info(f"Error Handler: ✓")

        logger.info("PricePilot API Phase 2 startup complete!")

    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise e

    yield

    # Shutdown
    logger.info("PricePilot API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="PricePilot API - Phase 2",
    description="Universal product price comparison with real worldwide search",
    version="2.0.0",
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


def get_error_handler() -> SearchErrorHandler:
    if error_handler is None:
        raise HTTPException(status_code=500, detail="Error handler not initialized")
    return error_handler


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with Phase 2 information"""
    return {
        "message": "🎯 PricePilot API - Phase 2 Complete!",
        "description": "Universal product price comparison with real worldwide search",
        "version": "2.0.0",
        "phase": "2 - Core Search Implementation",
        "features": [
            "Worldwide product search",
            "Multi-source aggregation (Google Shopping, Amazon, eBay, Local sites)",
            "Real-time price comparison",
            "Currency detection",
            "Async concurrent processing",
            "Robust error handling",
        ],
        "endpoints": {
            "health": "/health - Service status",
            "search": "/search - Main product search",
            "debug-search": "/debug-search - Raw search results",
            "test-services": "/test-services - Test all services",
            "countries": "/countries - Supported countries",
            "docs": "/docs - Interactive API documentation",
        },
        "example_usage": {
            "endpoint": "/search",
            "method": "POST",
            "body": {"country": "US", "query": "iPhone 16 Pro, 128GB"},
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check with detailed service status"""
    try:
        # Test service connections
        services_status = {}

        # Test SerpAPI
        if serpapi_client:
            serpapi_status = await serpapi_client.test_connection()
            services_status["serpapi"] = {
                "connected": serpapi_status["connected"],
                "message": serpapi_status.get("message", ""),
                "status": "Success" if serpapi_status["connected"] else "Failure",
            }

        # Test OpenAI
        if openai_client:
            openai_status = await openai_client.test_connection()
            services_status["openai"] = {
                "connected": openai_status["connected"],
                "message": openai_status.get("message", ""),
                "status": "Success" if openai_status["connected"] else "Failure",
            }

        # Check other services
        services_status["data_parser"] = {
            "connected": data_parser is not None,
            "message": "Data parser ready",
            "status": "Success" if data_parser else "Failure",
        }

        services_status["error_handler"] = {
            "connected": error_handler is not None,
            "message": "Error handler ready",
            "status": "Success" if error_handler else "Failure",
        }

        return HealthResponse(
            status="ok",
            message="PricePilot API Phase 2 - All systems operational",
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
    error_handler: SearchErrorHandler = Depends(get_error_handler),
):
    """
    🎯 Main product search endpoint - Phase 2 Complete Implementation

    What this does:
    1. Searches Google Shopping, Amazon, eBay, and local sites worldwide
    2. Parses and normalizes all results
    3. Returns clean, sorted product data

    Why: Provides comprehensive price comparison from global sources
    Returns: Structured list of products with prices, sorted by price
    """
    start_time = time.time()

    try:
        logger.info(f"Starting search: '{query.query}' in {query.country}")

        # Step 1: Execute multi-source search
        logger.info("Executing worldwide search across multiple sources...")
        raw_results = await serpapi.search_all_sources(query.query, query.country)

        # Step 2: Parse and normalize results
        logger.info("Parsing and normalizing results...")
        parsed_products = parser.parse_all_results(raw_results, query.country)

        # Step 3: Validate and convert to final format
        logger.info("Validating and formatting results...")
        final_results = []

        for product_data in parsed_products:
            try:
                # Validate using Pydantic model
                product_result = ProductResult(**product_data)
                final_results.append(product_result.dict())
            except Exception as e:
                logger.debug(f"Skipping invalid product: {str(e)}")
                continue

        # Step 4: Sort by price (lowest first)
        logger.info("Sorting by price...")
        try:
            final_results.sort(key=lambda x: float(x.get("price", "999999")))
        except Exception as e:
            logger.warning(f"Price sorting failed: {str(e)}")

        # Step 5: Calculate metrics
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
        search_time = time.time() - start_time
        logger.error(f"❌ Search failed after {search_time:.2f}s: {str(e)}")

        # Return error response but don't crash
        return SearchResponse(
            success=False,
            message=f"Search failed: {str(e)}",
            results=[],
            total_results=0,
            search_time_seconds=round(search_time, 2),
            country=query.country,
            query=query.query,
        )


@app.post("/debug-search")
async def debug_search(
    query: ProductQuery, serpapi: SerpAPIClient = Depends(get_serpapi_client)
):
    """🔍 Debug endpoint to inspect raw search results"""
    try:
        logger.info(f"🐛 Debug search: {query.query} in {query.country}")
        raw_results = await serpapi.search_all_sources(query.query, query.country)

        # Count results from each source
        result_counts = {}
        for source, data in raw_results.items():
            if "error" in data:
                result_counts[source] = f"ERROR: {data['error']}"
            else:
                # Count results based on source type
                if source == "google_shopping":
                    count = len(data.get("shopping_results", []))
                else:
                    count = len(data.get("organic_results", []))
                result_counts[source] = f"{count} results"

        return {
            "query": query.query,
            "country": query.country,
            "sources_attempted": list(raw_results.keys()),
            "result_counts": result_counts,
            "raw_results": raw_results,  # Full raw data for debugging
        }

    except Exception as e:
        logger.error(f"Debug search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test-services")
async def test_all_services(
    serpapi: SerpAPIClient = Depends(get_serpapi_client),
    openai: OpenAIClient = Depends(get_openai_client),
    error_handler: SearchErrorHandler = Depends(get_error_handler),
):
    """Test all services and show detailed status"""
    try:
        # Test SerpAPI
        serpapi_status = await serpapi.test_connection()

        # Test OpenAI
        openai_status = await openai.test_connection()

        # Get error summary
        error_summary = error_handler.get_error_summary()

        return {
            "timestamp": datetime.now().isoformat(),
            "phase": "2 - Core Search Implementation",
            "services": {
                "serpapi": serpapi_status,
                "openai": openai_status,
                "data_parser": {
                    "connected": data_parser is not None,
                    "message": "Data parser operational",
                },
                "error_handler": {
                    "connected": error_handler is not None,
                    "message": "Error handler operational",
                    "error_summary": error_summary,
                },
            },
            "overall_status": (
                "operational"
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
    """🌍 Get list of supported countries with details"""
    from app.models.product import CountryCode

    # Enhanced country information
    country_details = {
        "US": {"name": "United States", "currency": "USD", "symbol": "$"},
        "IN": {"name": "India", "currency": "INR", "symbol": "₹"},
        "UK": {"name": "United Kingdom", "currency": "GBP", "symbol": "£"},
        "CA": {"name": "Canada", "currency": "CAD", "symbol": "C$"},
        "AU": {"name": "Australia", "currency": "AUD", "symbol": "A$"},
        "DE": {"name": "Germany", "currency": "EUR", "symbol": "€"},
        "FR": {"name": "France", "currency": "EUR", "symbol": "€"},
        "JP": {"name": "Japan", "currency": "JPY", "symbol": "¥"},
        "BR": {"name": "Brazil", "currency": "BRL", "symbol": "R$"},
        "MX": {"name": "Mexico", "currency": "MXN", "symbol": "$"},
        "IT": {"name": "Italy", "currency": "EUR", "symbol": "€"},
        "ES": {"name": "Spain", "currency": "EUR", "symbol": "€"},
        "NL": {"name": "Netherlands", "currency": "EUR", "symbol": "€"},
    }

    return {
        "supported_countries": [country.value for country in CountryCode],
        "total_count": len(CountryCode),
        "country_details": country_details,
        "note": "More countries supported through general search",
    }


@app.get("/stats")
async def get_search_stats(
    error_handler: SearchErrorHandler = Depends(get_error_handler),
):
    """📊 Get search statistics and performance metrics"""
    try:
        error_summary = error_handler.get_error_summary()

        return {
            "timestamp": datetime.now().isoformat(),
            "phase": "2 - Core Search Implementation",
            "version": "2.0.0",
            "error_statistics": error_summary,
            "features_active": [
                "Multi-source search",
                "Price extraction",
                "Currency detection",
                "Error handling",
                "Result sorting",
            ],
            "next_phase": "3 - AI-Powered Enhancement",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
