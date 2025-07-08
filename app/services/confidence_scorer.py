import logging
from typing import List, Dict
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ConfidenceScorer:
    """
    Assigns confidence scores to products based on multiple factors
    
    What this does:
    - Evaluates product data quality
    - Considers source reliability
    - Incorporates AI validation scores
    - Assigns final confidence rating
    
    Why: Users need to know which results are most trustworthy
    How: Combines multiple quality signals into a single score
    """
    
    def __init__(self):
        # Trusted domains get higher confidence
        self.trusted_domains = {
            "apple.com": 10,
            "amazon.com": 9,
            "amazon.in": 9,
            "amazon.co.uk": 9,
            "bestbuy.com": 8,
            "walmart.com": 8,
            "target.com": 7,
            "flipkart.com": 8,
            "myntra.com": 7,
            "argos.co.uk": 7,
            "currys.co.uk": 6,
            "ebay.com": 5,
            "ebay.co.uk": 5
        }
    
    def score_products(self, products: List[Dict]) -> List[Dict]:
        """
        Add confidence scores to all products
        
        What this does: Calculates and adds confidence scores to each product
        Why: Helps users identify the most reliable results
        Returns: Products with added confidence_score field
        """
        if not products:
            return []
        
        logger.info(f"Calculating confidence scores for {len(products)} products")
        
        scored_products = []
        for product in products:
            confidence_score = self._calculate_confidence_score(product)
            
            # Add confidence score to product
            enhanced_product = product.copy()
            enhanced_product["confidence_score"] = confidence_score
            enhanced_product["confidence_level"] = self._get_confidence_level(confidence_score)
            
            scored_products.append(enhanced_product)
        
        # Sort by confidence score (highest first)
        scored_products.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        
        logger.info(f"Confidence scoring complete")
        
        return scored_products
    
    def _calculate_confidence_score(self, product: Dict) -> float:
        """Calculate confidence score for a single product (0-100)"""
        score = 0.0
        
        # 1. AI Validation Score (0-40 points)
        if product.get("ai_validated", False):
            ai_confidence = product.get("ai_confidence_score", 0)
            ai_relevance = product.get("ai_relevance_score", 0)
            
            # Weight AI scores heavily
            score += (ai_confidence * 0.25)  # Up to 25 points
            score += (ai_relevance * 0.15)   # Up to 15 points
        
        # 2. Source Reliability (0-20 points)
        domain_score = self._get_domain_score(product.get("link", ""))
        score += domain_score * 2  # Convert 0-10 to 0-20
        
        # 3. Data Quality (0-25 points)
        data_quality_score = self._assess_data_quality(product)
        score += data_quality_score
        
        # 4. Price Validity (0-15 points)
        price_score = self._assess_price_validity(product)
        score += price_score
        
        # 5. Bonus factors (0-10 points)
        bonus_score = self._calculate_bonus_score(product)
        score += bonus_score
        
        # Ensure score is within bounds
        return min(100.0, max(0.0, score))
    
    def _get_domain_score(self, url: str) -> float:
        """Get reliability score for the domain (0-10)"""
        if not url:
            return 0.0
        
        try:
            domain = urlparse(url).netloc.lower()
            
            # Remove www. prefix
            domain = re.sub(r'^www\.', '', domain)
            
            # Check against trusted domains
            for trusted_domain, score in self.trusted_domains.items():
                if domain == trusted_domain or domain.endswith('.' + trusted_domain):
                    return float(score)
            
            # Default score for unknown domains
            return 3.0
            
        except Exception:
            return 0.0
    
    def _assess_data_quality(self, product: Dict) -> float:
        """Assess the quality of product data (0-25 points)"""
        score = 0.0
        
        # Product name quality (0-8 points)
        product_name = product.get("productName", "")
        if product_name:
            if len(product_name) >= 10:
                score += 4
            if len(product_name) >= 20:
                score += 2
            if not any(spam in product_name.lower() for spam in ["click", "buy now", "limited"]):
                score += 2
        
        # Price availability (0-5 points)
        if product.get("price"):
            score += 3
            try:
                price_val = float(str(product["price"]).replace(',', ''))
                if price_val > 0:
                    score += 2
            except (ValueError, TypeError):
                pass
        
        # Currency information (0-3 points)
        if product.get("currency"):
            score += 3
        
        # Link validity (0-4 points)
        link = product.get("link", "")
        if link and link.startswith("http"):
            score += 2
            if len(link) > 20:  # Not just a basic URL
                score += 2
        
        # Additional data (0-5 points)
        if product.get("rating"):
            score += 2
        if product.get("image_url"):
            score += 1
        if product.get("availability"):
            score += 2
        
        return score
    
    def _assess_price_validity(self, product: Dict) -> float:
        """Assess if the price seems valid (0-15 points)"""
        score = 0.0
        
        price_str = product.get("price", "")
        currency = product.get("currency", "")
        
        if not price_str:
            return 0.0
        
        try:
            price_val = float(str(price_str).replace(',', ''))
            
            # Basic price validation (0-10 points)
            if price_val > 0:
                score += 5
            
            # Reasonable price range check (0-5 points)
            if 1 <= price_val <= 100000:  # Reasonable range for most products
                score += 3
            
            if 5 <= price_val <= 50000:   # More reasonable range
                score += 2
            
            # Currency consistency (0-5 points)
            if currency:
                score += 5
            
        except (ValueError, TypeError):
            # Invalid price format
            return 0.0
        
        return score
    
    def _calculate_bonus_score(self, product: Dict) -> float:
        """Calculate bonus points for special factors (0-10 points)"""
        score = 0.0
        
        # Duplicate removal bonus
        if product.get("duplicate_info"):
            # Products that survived duplicate removal are higher quality
            score += 3
        
        # Website name recognition
        website = product.get("website", "").lower()
        if website in ["amazon", "apple", "bestbuy", "walmart", "flipkart"]:
            score += 2
        
        # Rating availability
        rating = product.get("rating", "")
        if rating:
            try:
                rating_val = float(rating)
                if rating_val >= 4.0:
                    score += 3
                elif rating_val >= 3.0:
                    score += 1
            except (ValueError, TypeError):
                pass
        
        # Image availability
        if product.get("image_url"):
            score += 2
        
        return score
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert numeric score to confidence level"""
        if score >= 80:
            return "Very High"
        elif score >= 65:
            return "High"
        elif score >= 50:
            return "Medium"
        elif score >= 35:
            return "Low"
        else:
            return "Very Low"