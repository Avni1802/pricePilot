from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum


class CountryCode(str, Enum):
    """Supported country codes"""

    US = "US"
    IN = "IN"
    UK = "UK"
    CA = "CA"
    AU = "AU"
    DE = "DE"
    FR = "FR"
    JP = "JP"
    BR = "BR"
    MX = "MX"
    IT = "IT"
    ES = "ES"
    NL = "NL"


class ProductQuery(BaseModel):
    """Product search query model"""

    query: str = Field(
        ..., min_length=1, max_length=200, description="Product search query"
    )
    country: CountryCode = Field(..., description="Country code for localized search")

    class Config:
        schema_extra = {"example": {"query": "iPhone 16 Pro 128GB", "country": "US"}}


class ProductResult(BaseModel):
    """Enhanced product result model with AI fields"""

    link: str = Field(..., description="Product URL")
    price: str = Field(..., description="Product price (numeric string)")
    currency: str = Field(..., description="Currency code (USD, EUR, etc.)")
    productName: str = Field(..., description="Product name")
    website: str = Field(..., description="Website/store name")
    rating: Optional[str] = Field(default="", description="Product rating")
    availability: Optional[str] = Field(default="", description="Availability status")
    image_url: Optional[str] = Field(default="", description="Product image URL")

    # Phase 3: AI Enhancement Fields
    confidence_score: Optional[float] = Field(
        default=0.0, ge=0.0, le=100.0, description="Overall confidence score (0-100)"
    )
    confidence_level: Optional[str] = Field(
        default="",
        description="Confidence level (Very High, High, Medium, Low, Very Low)",
    )

    # AI Validation Fields
    ai_validated: Optional[bool] = Field(
        default=False, description="Whether product was validated by AI"
    )
    ai_relevance_score: Optional[float] = Field(
        default=0.0, ge=0.0, le=100.0, description="AI relevance score (0-100)"
    )
    ai_confidence_score: Optional[float] = Field(
        default=0.0, ge=0.0, le=100.0, description="AI confidence score (0-100)"
    )
    ai_clean_name: Optional[str] = Field(
        default="", description="AI-cleaned product name"
    )
    ai_is_relevant: Optional[bool] = Field(
        default=False, description="AI relevance determination"
    )
    ai_reason: Optional[str] = Field(
        default="", description="AI reasoning for validation"
    )

    # Duplicate Removal Fields
    duplicate_info: Optional[Dict[str, Any]] = Field(
        default=None, description="Information about duplicate removal"
    )

    @validator("price")
    def validate_price(cls, v):
        """Ensure price is a valid numeric string"""
        if not v:
            return "0"
        try:
            # Remove commas and validate it's a number
            clean_price = str(v).replace(",", "")
            float(clean_price)
            return clean_price
        except ValueError:
            return "0"

    @validator("link")
    def validate_link(cls, v):
        """Ensure link is a valid URL"""
        if not v or not v.startswith("http"):
            return ""
        return v

    class Config:
        schema_extra = {
            "example": {
                "link": "https://www.apple.com/iphone-16-pro/",
                "price": "999.00",
                "currency": "USD",
                "productName": "Apple iPhone 16 Pro 128GB",
                "website": "Apple",
                "rating": "4.5",
                "availability": "In Stock",
                "image_url": "https://example.com/image.jpg",
                "confidence_score": 95.5,
                "confidence_level": "Very High",
                "ai_validated": True,
                "ai_relevance_score": 98.0,
                "ai_confidence_score": 92.0,
                "ai_clean_name": "Apple iPhone 16 Pro 128GB",
                "ai_is_relevant": True,
                "ai_reason": "Exact match for iPhone 16 Pro with correct specifications",
            }
        }


class SearchResponse(BaseModel):
    """Enhanced search response model"""

    success: bool = Field(..., description="Whether the search was successful")
    message: str = Field(..., description="Response message")
    results: List[ProductResult] = Field(..., description="List of product results")
    total_results: int = Field(..., description="Total number of results")
    search_time_seconds: float = Field(..., description="Search execution time")
    country: str = Field(..., description="Country searched")
    query: str = Field(..., description="Search query used")

    # Phase 3: AI Enhancement Metadata
    ai_enhanced: Optional[bool] = Field(
        default=True, description="Whether AI enhancement was used"
    )
    pipeline_stats: Optional[Dict[str, Any]] = Field(
        default=None, description="Pipeline processing statistics"
    )

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Found 5 AI-validated products for 'iPhone 16 Pro' in US",
                "results": [],
                "total_results": 5,
                "search_time_seconds": 8.2,
                "country": "US",
                "query": "iPhone 16 Pro",
                "ai_enhanced": True,
                "pipeline_stats": {
                    "raw_products": 25,
                    "ai_validated": 15,
                    "after_deduplication": 8,
                    "final_results": 5,
                },
            }
        }


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str = Field(..., description="Overall health status")
    message: str = Field(..., description="Health check message")
    timestamp: str = Field(..., description="Timestamp of health check")
    services: Dict[str, Dict[str, Any]] = Field(
        ..., description="Individual service statuses"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "ok",
                "message": "PricePilot API Phase 3 - AI-enhanced systems operational",
                "timestamp": "2024-01-01T12:00:00",
                "services": {
                    "serpapi": {
                        "connected": True,
                        "message": "SerpAPI connection successful",
                        "status": "✅",
                    },
                    "openai": {
                        "connected": True,
                        "message": "OpenAI connection successful",
                        "status": "✅",
                    },
                    "ai_validator": {
                        "connected": True,
                        "message": "AI validator ready",
                        "status": "✅",
                    },
                },
            }
        }
