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
from app.services.ai_validator import AIProductValidator
from app.services.duplicate_remover import DuplicateRemover
from app.services.confidence_scorer import ConfidenceScorer

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
ai_validator = None
duplicate_remover = None
confidence_scorer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global serpapi_client, openai_client, data_parser, error_handler
    global ai_validator, duplicate_remover, confidence_scorer

    logger.info("Starting PricePilot API - Phase 3...")

    try:
        # Initialize all services
        serpapi_client = SerpAPIClient()
        openai_client = OpenAIClient()
        data_parser = ProductDataParser()
        error_handler = SearchErrorHandler()

        # Initialize Phase 3 AI services
        ai_validator = AIProductValidator()
        duplicate_remover = DuplicateRemover()
        confidence_scorer = ConfidenceScorer()

        logger.info("All services initialized successfully")

        # Test connections
        serpapi_status = await serpapi_client.test_connection()
        openai_status = await openai_client.test_connection()
        ai_validator_status = await ai_validator.test_connection()

        logger.info(
            f"SerpAPI: {'Success' if serpapi_status['connected'] else 'Failure'}"
        )
        logger.info(f"OpenAI: {'Success' if openai_status['connected'] else 'Failure'}")
        logger.info(
            f"AI Validator: {'Success' if ai_validator_status['connected'] else 'Success'}"
        )
        logger.info(f"Data Parser: Success")
        logger.info(f"Duplicate Remover: Success")
        logger.info(f"Confidence Scorer: Success")
        logger.info(f"Error Handler: Success")

        logger.info("PricePilot API Phase 3 startup complete!")

    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise e

    yield

    logger.info("PricePilot API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="PricePilot API - Phase 3",
    description="AI-powered universal product price comparison with intelligent validation",
    version="3.0.0",
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


# Dependency functions
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


def get_ai_validator() -> AIProductValidator:
    if ai_validator is None:
        raise HTTPException(status_code=500, detail="AI validator not initialized")
    return ai_validator


def get_duplicate_remover() -> DuplicateRemover:
    if duplicate_remover is None:
        raise HTTPException(status_code=500, detail="Duplicate remover not initialized")
    return duplicate_remover


def get_confidence_scorer() -> ConfidenceScorer:
    if confidence_scorer is None:
        raise HTTPException(status_code=500, detail="Confidence scorer not initialized")
    return confidence_scorer


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with Phase 3 information"""
    return {
        "message": "🧠 PricePilot API - Phase 3 Complete!",
        "description": "AI-powered universal product price comparison with intelligent validation",
        "version": "3.0.0",
        "phase": "3 - AI-Powered Enhancement ✅",
        "features": [
            "Worldwide product search",
            "Multi-source aggregation (Google Shopping, Amazon, eBay, Local sites)",
            "AI-powered product validation (GPT-4o-mini)",
            "Intelligent relevance filtering",
            "Smart duplicate removal",
            "Confidence scoring system",
            "Enhanced price comparison",
            "Currency detection",
            "Async concurrent processing",
            "Robust error handling",
        ],
        "ai_enhancements": [
            "Product relevance validation",
            "Clean product name extraction",
            "Duplicate detection and removal",
            "Multi-factor confidence scoring",
            "Quality-based result ranking",
        ],
        "endpoints": {
            "health": "/health - Service status",
            "search": "/search - AI-enhanced product search",
            "search-basic": "/search-basic - Phase 2 search without AI",
            "test-ai": "/test-ai - Test AI validation",
            "debug-search": "/debug-search - Raw search results",
            "test-services": "/test-services - Test all services",
            "countries": "/countries - Supported countries",
            "docs": "/docs - Interactive API documentation",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check with Phase 3 AI services"""
    try:
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

        # Test AI Validator
        if ai_validator:
            ai_validator_status = await ai_validator.test_connection()
            services_status["ai_validator"] = {
                "connected": ai_validator_status["connected"],
                "message": ai_validator_status.get("message", ""),
                "status": "Success" if ai_validator_status["connected"] else "Failure",
            }

        # Check other services
        services_status["data_parser"] = {
            "connected": data_parser is not None,
            "message": "Data parser ready",
            "status": "Success" if data_parser else "Failure",
        }

        services_status["duplicate_remover"] = {
            "connected": duplicate_remover is not None,
            "message": "Duplicate remover ready",
            "status": "Success" if duplicate_remover else "Failure",
        }

        services_status["confidence_scorer"] = {
            "connected": confidence_scorer is not None,
            "message": "Confidence scorer ready",
            "status": "Success" if confidence_scorer else "Failure",
        }

        services_status["error_handler"] = {
            "connected": error_handler is not None,
            "message": "Error handler ready",
            "status": "Success" if error_handler else "Failure",
        }

        return HealthResponse(
            status="ok",
            message="PricePilot API Phase 3 - AI-enhanced systems operational",
            timestamp=datetime.now().isoformat(),
            services=services_status,
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_products_ai_enhanced(
    query: ProductQuery,
    serpapi: SerpAPIClient = Depends(get_serpapi_client),
    openai: OpenAIClient = Depends(get_openai_client),
    parser: ProductDataParser = Depends(get_data_parser),
    ai_validator: AIProductValidator = Depends(get_ai_validator),
    duplicate_remover: DuplicateRemover = Depends(get_duplicate_remover),
    confidence_scorer: ConfidenceScorer = Depends(get_confidence_scorer),
    error_handler: SearchErrorHandler = Depends(get_error_handler),
):
    """
    🧠 AI-Enhanced Product Search - Phase 3 Complete Implementation

    What this does:
    1. Searches multiple sources worldwide (Phase 2)
    2. Uses AI to validate product relevance (Phase 3)
    3. Removes duplicates intelligently (Phase 3)
    4. Assigns confidence scores (Phase 3)
    5. Returns high-quality, validated results

    Why: Provides the most accurate and relevant product matches
    Returns: AI-validated, deduplicated products with confidence scores
    """
    start_time = time.time()

    try:
        logger.info(f"Starting AI-enhanced search: '{query.query}' in {query.country}")

        # Step 1: Execute multi-source search (Phase 2)
        logger.info("📡 Step 1: Executing worldwide search...")
        raw_results = await serpapi.search_all_sources(query.query, query.country)

        # Step 2: Parse and normalize results (Phase 2)
        logger.info("Step 2: Parsing and normalizing results...")
        parsed_products = parser.parse_all_results(raw_results, query.country)

        if not parsed_products:
            logger.warning("No products found after parsing")
            return SearchResponse(
                success=True,
                message=f"No products found for '{query.query}' in {query.country}",
                results=[],
                total_results=0,
                search_time_seconds=round(time.time() - start_time, 2),
                country=query.country,
                query=query.query,
            )

        logger.info(f"Found {len(parsed_products)} raw products")

        # Step 3: AI validation (Phase 3 - NEW)
        logger.info("Step 3: AI validation and relevance filtering...")
        ai_validated_products = await ai_validator.validate_products(
            parsed_products, query.query, query.country
        )

        logger.info(
            f"AI validation: {len(ai_validated_products)}/{len(parsed_products)} products passed"
        )

        # Step 4: Remove duplicates (Phase 3 - NEW)
        logger.info("Step 4: Removing duplicates...")
        unique_products = duplicate_remover.remove_duplicates(ai_validated_products)

        logger.info(f"Duplicate removal: {len(unique_products)} unique products")

        # Step 5: Calculate confidence scores (Phase 3 - NEW)
        logger.info("Step 5: Calculating confidence scores...")
        scored_products = confidence_scorer.score_products(unique_products)

        # Step 6: Validate and convert to final format
        logger.info("Step 6: Final validation and formatting...")
        final_results = []

        for product_data in scored_products:
            try:
                # Validate using Pydantic model
                product_result = ProductResult(**product_data)
                final_results.append(product_result.dict())
            except Exception as e:
                logger.debug(f"Skipping invalid product: {str(e)}")
                continue

        # Step 7: Final sorting by confidence score (highest first)
        logger.info("Step 7: Final ranking by confidence...")
        final_results.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)

        # Step 8: Calculate metrics
        search_time = time.time() - start_time

        # Step 9: Log success metrics
        sources_used = [k for k, v in raw_results.items() if "error" not in v]
        sources_failed = [k for k, v in raw_results.items() if "error" in v]

        logger.info(f"AI-enhanced search completed successfully!")
        logger.info(
            f"Pipeline: {len(parsed_products)} → {len(ai_validated_products)} → {len(unique_products)} → {len(final_results)}"
        )
        logger.info(f"⏱Time: {search_time:.2f} seconds")
        logger.info(f"Sources used: {sources_used}")
        if sources_failed:
            logger.warning(f"❌ Sources failed: {sources_failed}")

        return SearchResponse(
            success=True,
            message=f"Found {len(final_results)} AI-validated products for '{query.query}' in {query.country}",
            results=final_results,
            total_results=len(final_results),
            search_time_seconds=round(search_time, 2),
            country=query.country,
            query=query.query,
        )

    except Exception as e:
        search_time = time.time() - start_time
        logger.error(f"AI-enhanced search failed after {search_time:.2f}s: {str(e)}")

        # Return error response but don't crash
        return SearchResponse(
            success=False,
            message=f"AI-enhanced search failed: {str(e)}",
            results=[],
            total_results=0,
            search_time_seconds=round(search_time, 2),
            country=query.country,
            query=query.query,
        )


@app.post("/search-basic", response_model=SearchResponse)
async def search_products_basic(
    query: ProductQuery,
    serpapi: SerpAPIClient = Depends(get_serpapi_client),
    parser: ProductDataParser = Depends(get_data_parser),
    error_handler: SearchErrorHandler = Depends(get_error_handler),
):
    """
    🔍 Basic Product Search - Phase 2 Implementation (without AI)

    What this does: Phase 2 search without AI enhancements
    Why: Fallback option and comparison baseline
    Returns: Raw search results without AI validation
    """
    start_time = time.time()

    try:
        logger.info(f"Starting basic search: '{query.query}' in {query.country}")

        # Execute Phase 2 search pipeline
        raw_results = await serpapi.search_all_sources(query.query, query.country)
        parsed_products = parser.parse_all_results(raw_results, query.country)

        # Basic validation and formatting
        final_results = []
        for product_data in parsed_products:
            try:
                product_result = ProductResult(**product_data)
                final_results.append(product_result.dict())
            except Exception as e:
                logger.debug(f"Skipping invalid product: {str(e)}")
                continue

        # Sort by price (lowest first)
        try:
            final_results.sort(key=lambda x: float(x.get("price", "999999")))
        except Exception as e:
            logger.warning(f"Price sorting failed: {str(e)}")

        search_time = time.time() - start_time

        return SearchResponse(
            success=True,
            message=f"Found {len(final_results)} products (basic search) for '{query.query}' in {query.country}",
            results=final_results,
            total_results=len(final_results),
            search_time_seconds=round(search_time, 2),
            country=query.country,
            query=query.query,
        )

    except Exception as e:
        search_time = time.time() - start_time
        logger.error(f"Basic search failed: {str(e)}")

        return SearchResponse(
            success=False,
            message=f"Basic search failed: {str(e)}",
            results=[],
            total_results=0,
            search_time_seconds=round(search_time, 2),
            country=query.country,
            query=query.query,
        )


@app.post("/test-ai")
async def test_ai_validation(
    query: ProductQuery, ai_validator: AIProductValidator = Depends(get_ai_validator)
):
    """🧪 Test AI validation with sample products"""
    try:
        # Create sample products for testing
        sample_products = [
            {
                "productName": f"{query.query} - Genuine Product",
                "price": "299.99",
                "currency": "USD",
                "website": "TestStore",
                "link": "https://example.com/product1",
            },
            {
                "productName": "Completely Unrelated Product",
                "price": "19.99",
                "currency": "USD",
                "website": "TestStore",
                "link": "https://example.com/product2",
            },
            {
                "productName": f"Best {query.query} Deal - Buy Now!",
                "price": "199.99",
                "currency": "USD",
                "website": "TestStore",
                "link": "https://example.com/product3",
            },
        ]

        logger.info(
            f"🧪 Testing AI validation with {len(sample_products)} sample products"
        )

        # Test AI validation
        validated_products = await ai_validator.validate_products(
            sample_products, query.query, query.country
        )

        return {
            "message": "AI validation test completed",
            "query": query.query,
            "country": query.country,
            "original_products": len(sample_products),
            "validated_products": len(validated_products),
            "sample_input": sample_products,
            "ai_results": validated_products,
            "ai_working": len(validated_products) > 0,
        }

    except Exception as e:
        logger.error(f"AI validation test failed: {str(e)}")
        return {
            "message": "AI validation test failed",
            "error": str(e),
            "ai_working": False,
        }


@app.get("/test-services")
async def test_all_services():
    """🧪 Test all services including Phase 3 AI components"""
    try:
        results = {}

        # Test SerpAPI
        if serpapi_client:
            serpapi_status = await serpapi_client.test_connection()
            results["serpapi"] = serpapi_status

        # Test OpenAI
        if openai_client:
            openai_status = await openai_client.test_connection()
            results["openai"] = openai_status

        # Test AI Validator
        if ai_validator:
            ai_validator_status = await ai_validator.test_connection()
            results["ai_validator"] = ai_validator_status

        # Test other services
        results["data_parser"] = {
            "connected": data_parser is not None,
            "message": "Data parser ready",
        }

        results["duplicate_remover"] = {
            "connected": duplicate_remover is not None,
            "message": "Duplicate remover ready",
        }

        results["confidence_scorer"] = {
            "connected": confidence_scorer is not None,
            "message": "Confidence scorer ready",
        }

        results["error_handler"] = {
            "connected": error_handler is not None,
            "message": "Error handler ready",
        }

        # Overall status
        all_connected = all(
            service.get("connected", False) for service in results.values()
        )

        return {
            "message": "Service test completed",
            "all_services_working": all_connected,
            "phase": "3 - AI-Powered Enhancement",
            "services": results,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Service test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service test failed: {str(e)}")


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
        "ai_enhanced": True,
        "phase": "3 - AI-Powered Enhancement",
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
            "phase": "3 - AI-Powered Enhancement ✅",
            "version": "3.0.0",
            "error_statistics": error_summary,
            "features_active": [
                "Multi-source search",
                "AI product validation",
                "Intelligent duplicate removal",
                "Confidence scoring",
                "Price extraction",
                "Currency detection",
                "Error handling",
                "Result ranking",
            ],
            "ai_features": [
                "GPT-4o-mini product validation",
                "Relevance scoring",
                "Clean name extraction",
                "Quality assessment",
                "Confidence calculation",
            ],
            "next_phase": "4 - Global Coverage & Optimization",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
