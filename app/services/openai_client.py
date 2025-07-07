import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging
import json
from typing import Dict, List, Optional

load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Client for interacting with OpenAI GPT-4o-mini"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"  # Using the cost-effective model
    
    async def test_connection(self) -> Dict:
        """Test OpenAI connection"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Hello, this is a connection test. Please respond with 'Connection successful'."}
                ],
                max_tokens=10
            )
            
            if response.choices and response.choices[0].message:
                return {
                    "connected": True,
                    "message": "OpenAI connection successful",
                    "model": self.model,
                    "response": response.choices[0].message.content
                }
            else:
                return {
                    "connected": False,
                    "message": "OpenAI connection failed - no response"
                }
                
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {str(e)}")
            return {
                "connected": False,
                "error": str(e),
                "message": "OpenAI connection test failed"
            }
    
    async def validate_products(self, raw_results: List[Dict], original_query: str) -> List[Dict]:
        """Use GPT-4o-mini to validate and enhance product matches"""
        try:
            # We'll implement this in Phase 3
            # For now, just return empty list
            return []
            
        except Exception as e:
            logger.error(f"Product validation failed: {str(e)}")
            return []