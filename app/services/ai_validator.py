import logging
from typing import List, Dict, Optional, Tuple
import json
import asyncio
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AIProductValidator:
    """
    Uses OpenAI GPT-4o-mini to validate and enhance product search results
    
    What this does: 
    - Validates if products match the search query
    - Extracts clean product information
    - Assigns confidence scores
    - Removes irrelevant results
    
    Why: Raw search results contain noise, duplicates, and irrelevant items
    How: Uses AI to understand context and product relevance
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"  # Fast and cost-effective
        
        # Validation prompt template
        self.validation_prompt = """
You are a product validation expert. Analyze if these search results match the user's query.

USER QUERY: "{query}"
COUNTRY: {country}

PRODUCTS TO VALIDATE:
{products_json}

For each product, determine:
1. RELEVANCE: Does this product match the user's query? (0-100 score)
2. CLEAN_NAME: Extract a clean, standardized product name
3. CONFIDENCE: Overall confidence this is a good match (0-100)
4. REASON: Brief explanation of your decision

Return ONLY a JSON array with this exact format:
[
  {{
    "original_index": 0,
    "relevance_score": 85,
    "clean_name": "Apple iPhone 16 Pro 128GB",
    "confidence_score": 90,
    "is_relevant": true,
    "reason": "Exact match for iPhone 16 Pro"
  }}
]

Rules:
- Only include products with relevance_score >= 60
- is_relevant = true only if relevance_score >= 70
- Be strict about product matching
- Remove obvious spam/unrelated items
"""

    async def validate_products(self, products: List[Dict], query: str, country: str) -> List[Dict]:
        """
        Validate products using AI and return only relevant matches
        
        What this does: Sends products to AI for validation and filtering
        Why: Removes irrelevant results and improves search quality
        Returns: List of AI-validated products with confidence scores
        """
        if not products:
            logger.info("No products to validate")
            return []
        
        logger.info(f"Starting AI validation for {len(products)} products")
        
        try:
            # Prepare products for AI analysis (limit to essential fields)
            products_for_ai = []
            for i, product in enumerate(products):
                products_for_ai.append({
                    "index": i,
                    "name": product.get("productName", ""),
                    "price": product.get("price", ""),
                    "currency": product.get("currency", ""),
                    "website": product.get("website", ""),
                    "link": product.get("link", "")[:100]  # Truncate long URLs
                })
            
            # Split into batches if too many products (AI has token limits)
            batch_size = 10
            validated_products = []
            
            for i in range(0, len(products_for_ai), batch_size):
                batch = products_for_ai[i:i + batch_size]
                batch_results = await self._validate_batch(batch, query, country)
                
                # Merge AI results back with original product data
                for ai_result in batch_results:
                    original_index = ai_result.get("original_index", 0)
                    if original_index < len(products):
                        # Enhance original product with AI insights
                        enhanced_product = products[original_index].copy()
                        enhanced_product.update({
                            "ai_relevance_score": ai_result.get("relevance_score", 0),
                            "ai_confidence_score": ai_result.get("confidence_score", 0),
                            "ai_clean_name": ai_result.get("clean_name", ""),
                            "ai_is_relevant": ai_result.get("is_relevant", False),
                            "ai_reason": ai_result.get("reason", ""),
                            "ai_validated": True
                        })
                        
                        # Use AI's clean name if it's better
                        if ai_result.get("clean_name") and len(ai_result["clean_name"]) > 5:
                            enhanced_product["productName"] = ai_result["clean_name"]
                        
                        validated_products.append(enhanced_product)
                
                # Small delay between batches to avoid rate limits
                if i + batch_size < len(products_for_ai):
                    await asyncio.sleep(0.5)
            
            # Filter to only relevant products
            relevant_products = [
                p for p in validated_products 
                if p.get("ai_is_relevant", False) and p.get("ai_relevance_score", 0) >= 70
            ]
            
            logger.info(f"AI validation complete: {len(relevant_products)}/{len(products)} products passed")
            
            return relevant_products
            
        except Exception as e:
            logger.error(f"AI validation failed: {str(e)}")
            # Fallback: return original products without AI enhancement
            logger.info("Falling back to original products without AI validation")
            return products

    async def _validate_batch(self, products_batch: List[Dict], query: str, country: str) -> List[Dict]:
        """Validate a batch of products using AI"""
        try:
            # Format products for AI
            products_json = json.dumps(products_batch, indent=2)
            
            # Create the prompt
            prompt = self.validation_prompt.format(
                query=query,
                country=country,
                products_json=products_json
            )
            
            logger.debug(f"Sending batch of {len(products_batch)} products to AI")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a product validation expert. Return only valid JSON arrays."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=2000
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content.strip()
            
            # Clean up response (remove markdown formatting if present)
            if ai_response.startswith(""):
                ai_response = ai_response.replace("json", "").replace("```", "").strip()
            
            # Parse JSON
            validation_results = json.loads(ai_response)
            
            logger.debug(f"AI validated {len(validation_results)} products in batch")
            
            return validation_results
            
        except json.JSONDecodeError as e:
            logger.error(f"AI returned invalid JSON: {str(e)}")
            logger.debug(f"AI Response: {ai_response[:200]}...")
            return []
            
        except Exception as e:
            logger.error(f"AI validation batch failed: {str(e)}")
            return []

    async def test_connection(self) -> Dict:
        """Test AI service connection"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Hello, respond with just 'OK' if you can hear me."}
                ],
                max_tokens=10
            )
            
            return {
                "connected": True,
                "message": "AI validator connection successful",
                "model": self.model
            }
            
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "message": "AI validator connection failed"
            }