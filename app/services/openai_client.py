import os
import logging
from typing import Dict
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    OpenAI client for general AI operations

    What this does: Provides a general OpenAI client for various AI tasks
    Why: Centralized OpenAI configuration and connection management
    How: Wraps the OpenAI API with error handling and testing
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"

    async def test_connection(self) -> Dict:
        """Test OpenAI API connection"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello, respond with just 'OK' if you can hear me.",
                    }
                ],
                max_tokens=10,
                temperature=0,
            )

            response_text = response.choices[0].message.content.strip()

            return {
                "connected": True,
                "message": "OpenAI connection successful",
                "model": self.model,
                "test_response": response_text,
            }

        except Exception as e:
            logger.error(f"OpenAI connection test failed: {str(e)}")
            return {
                "connected": False,
                "error": str(e),
                "message": "OpenAI connection failed",
            }

    async def generate_completion(self, prompt: str, max_tokens: int = 100) -> str:
        """Generate a completion for a given prompt"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI completion failed: {str(e)}")
            raise e
