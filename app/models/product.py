from pydantic import BaseModel, Field
from typing import List, Optional
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

class ProductQuery(BaseModel):
    """Input model for product search"""
    country: CountryCode = Field(..., description="Country code for search")
    query: str = Field(..., min_length=1, max_length=200, description="Product search query")
    
    class Config:
        json_schema_extra = {
            "example": {
                "country": "US",
                "query": "iPhone 16 Pro, 128GB"
            }
        }

class ProductResult(BaseModel):
    """Output model for product results"""
    link: str = Field(..., description="Product URL")
    price: str = Field(..., description="Product price")
    currency: str = Field(..., description="Currency code")
    productName: str = Field(..., description="Product name")
    website: str = Field(..., description="Website/store name")
    rating: Optional[str] = Field(None, description="Product rating")
    availability: Optional[str] = Field(None, description="Stock availability")
    image_url: Optional[str] = Field(None, description="Product image URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "link": "https://apple.com/iphone-16-pro",
                "price": "999.00",
                "currency": "USD",
                "productName": "Apple iPhone 16 Pro 128GB",
                "website": "Apple Store",
                "rating": "4.5",
                "availability": "In Stock",
                "image_url": "https://example.com/image.jpg"
            }
        }

class SearchResponse(BaseModel):
    """Response wrapper for search results"""
    success: bool
    message: str
    results: List[ProductResult]
    total_results: int
    search_time_seconds: float
    country: str
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Search completed successfully",
                "results": [],
                "total_results": 0,
                "search_time_seconds": 2.5,
                "country": "US",
                "query": "iPhone 16 Pro"
            }
        }

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    timestamp: str
    version: str = "1.0.0"
    services: dict = Field(default_factory=dict)