import os
from typing import Dict, List, Optional, Tuple
import httpx
from serpapi import GoogleSearch
from dotenv import load_dotenv
import asyncio
import logging

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)


class SerpAPIClient:
    """Enhanced client for worldwide product search via SerpAPI"""

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_KEY environment variable is required")

        # Simplified and working domain mapping
        self.amazon_domains = {
            "US": "amazon.com",
            "IN": "amazon.in", 
            "UK": "amazon.co.uk",
            "CA": "amazon.ca",
            "AU": "amazon.com.au",
            "DE": "amazon.de",
            "FR": "amazon.fr",
            "IT": "amazon.it",
            "ES": "amazon.es"
        }

        # Simplified local sites for Google search
        self.local_sites = {
            "US": ["walmart.com", "bestbuy.com", "target.com"],
            "IN": ["flipkart.com", "snapdeal.com", "myntra.com"],
            "UK": ["argos.co.uk", "currys.co.uk", "very.co.uk"],
            "CA": ["canadiantire.ca", "bestbuy.ca"],
            "AU": ["jbhifi.com.au", "harveynorman.com.au"],
            "DE": ["otto.de", "mediamarkt.de"],
            "FR": ["fnac.com", "darty.com"],
            "IT": ["eprice.it", "unieuro.it"],
            "ES": ["elcorteingles.es", "mediamarkt.es"]
        }

        # eBay domain mapping (simplified)
        self.ebay_domains = {
            "US": "ebay.com",
            "UK": "ebay.co.uk", 
            "CA": "ebay.ca",
            "AU": "ebay.com.au",
            "DE": "ebay.de",
            "FR": "ebay.fr",
            "IT": "ebay.it",
            "ES": "ebay.es"
        }

    async def search_all_sources(self, query: str, country: str) -> Dict[str, Dict]:
        """
        Search all available sources for a product with improved error handling
        """
        logger.info(f"Starting comprehensive search for '{query}' in {country}")

        # Create search tasks for concurrent execution
        search_tasks = []

        # 1. Google Shopping (primary source - most reliable)
        search_tasks.append(
            ("google_shopping", self.search_google_shopping(query, country))
        )

        # 2. Amazon (only if domain exists and with correct parameters)
        if country in self.amazon_domains:
            search_tasks.append(
                ("amazon", self.search_amazon_fixed(query, country))
            )

        # 3. Google general search (simplified)
        search_tasks.append(
            ("google_general", self.search_google_simple(query, country))
        )

        # 4. eBay (with correct parameters)
        if country in self.ebay_domains:
            search_tasks.append(
                ("ebay", self.search_ebay_fixed(query, country))
            )

        # Execute searches with individual error handling
        results = {}

        for search_name, search_future in search_tasks:
            try:
                logger.info(f"Executing {search_name} search...")
                result = await asyncio.wait_for(search_future, timeout=15.0)
                results[search_name] = result
                logger.info(f"{search_name} search completed")
            except asyncio.TimeoutError:
                logger.error(f"{search_name} search timed out")
                results[search_name] = {"error": "Search timed out"}
            except Exception as e:
                logger.error(f"{search_name} search failed: {str(e)}")
                results[search_name] = {"error": str(e)}

        logger.info(f"Search completed. Working sources: {[k for k, v in results.items() if 'error' not in v]}")
        return results

    async def search_google_shopping(self, query: str, country: str) -> Dict:
        """Google Shopping search - most reliable"""
        try:
            search_params = {
                "engine": "google_shopping",
                "q": query,
                "gl": country.lower(),
                "hl": "en",
                "api_key": self.api_key,
                "num": 20
            }

            logger.info(f"Google Shopping: {query} in {country}")

            loop = asyncio.get_event_loop()
            search = GoogleSearch(search_params)
            result = await loop.run_in_executor(None, search.get_dict)

            if "error" in result:
                logger.error(f"Google Shopping API error: {result['error']}")
                return {"error": result["error"]}

            shopping_results = result.get('shopping_results', [])
            logger.info(f"Google Shopping: Found {len(shopping_results)} products")

            return result

        except Exception as e:
            logger.error(f"Google Shopping search failed: {str(e)}")
            return {"error": str(e)}

    async def search_amazon_fixed(self, query: str, country: str) -> Dict:
        """Fixed Amazon search with correct parameters"""
        try:
            domain = self.amazon_domains.get(country, "amazon.com")

            # FIXED: Use 'k' parameter for Amazon search (not 'q')
            search_params = {
                "engine": "amazon",
                "amazon_domain": domain,
                "k": query,  # FIXED: Amazon uses 'k' parameter, not 'q'
                "api_key": self.api_key
            }

            logger.info(f"Amazon: {query} on {domain}")

            loop = asyncio.get_event_loop()
            search = GoogleSearch(search_params)
            result = await loop.run_in_executor(None, search.get_dict)

            if "error" in result:
                logger.error(f"Amazon API error: {result['error']}")
                return {"error": result["error"]}

            # Check for results in different possible fields
            organic_results = result.get('organic_results', [])
            products = result.get('products', [])  # Sometimes Amazon returns 'products'

            if not organic_results and products:
                result['organic_results'] = products
                organic_results = products

            logger.info(f"Amazon: Found {len(organic_results)} products")
            return result

        except Exception as e:
            logger.error(f"Amazon search failed: {str(e)}")
            return {"error": str(e)}

    async def search_google_simple(self, query: str, country: str) -> Dict:
        """Simplified Google general search"""
        try:
            # Much simpler query - just add "buy" and "price"
            enhanced_query = f"{query} buy price online"

            search_params = {
                "engine": "google",
                "q": enhanced_query,
                "gl": country.lower(),
                "hl": "en",
                "api_key": self.api_key,
                "num": 10  # Fewer results to avoid issues
            }

            logger.info(f"Google general: {enhanced_query}")

            loop = asyncio.get_event_loop()
            search = GoogleSearch(search_params)
            result = await loop.run_in_executor(None, search.get_dict)

            if "error" in result:
                logger.error(f"Google general API error: {result['error']}")
                return {"error": result["error"]}

            organic_results = result.get('organic_results', [])
            logger.info(f"Google general: Found {len(organic_results)} results")

            return result

        except Exception as e:
            logger.error(f"Google general search failed: {str(e)}")
            return {"error": str(e)}

    async def search_ebay_fixed(self, query: str, country: str) -> Dict:
        """Fixed eBay search with correct parameters"""
        try:
            domain = self.ebay_domains.get(country, "ebay.com")

            # FIXED: Use '_nkw' parameter for eBay search (not 'q')
            search_params = {
                "engine": "ebay",
                "ebay_domain": domain,
                "_nkw": query,  # FIXED: eBay uses '_nkw' parameter, not 'q'
                "api_key": self.api_key
            }

            logger.info(f"eBay: {query} on {domain}")

            loop = asyncio.get_event_loop()
            search = GoogleSearch(search_params)
            result = await loop.run_in_executor(None, search.get_dict)

            if "error" in result:
                logger.error(f"eBay API error: {result['error']}")
                return {"error": result["error"]}

            organic_results = result.get('organic_results', [])
            logger.info(f"eBay: Found {len(organic_results)} products")

            return result

        except Exception as e:
            logger.error(f"eBay search failed: {str(e)}")
            return {"error": str(e)}

    async def test_connection(self) -> Dict:
        """Test SerpAPI connection"""
        try:
            search_params = {
                "engine": "google",
                "q": "test",
                "api_key": self.api_key,
                "num": 1
            }

            loop = asyncio.get_event_loop()
            search = GoogleSearch(search_params)
            result = await loop.run_in_executor(None, search.get_dict)

            if "error" in result:
                return {
                    "connected": False,
                    "error": result["error"],
                    "message": "SerpAPI connection failed"
                }

            return {
                "connected": True,
                "message": "SerpAPI connection successful"
            }

        except Exception as e:
            logger.error(f"SerpAPI connection test failed: {str(e)}")
            return {
                "connected": False,
                "error": str(e),
                "message": "SerpAPI connection test failed"
            }
