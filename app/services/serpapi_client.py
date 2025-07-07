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
        
        # Worldwide domain mapping for comprehensive coverage
        self.amazon_domains = {
            "US": "amazon.com",
            "IN": "amazon.in", 
            "UK": "amazon.co.uk",
            "CA": "amazon.ca",
            "AU": "amazon.com.au",
            "DE": "amazon.de",
            "FR": "amazon.fr",
            "JP": "amazon.co.jp",
            "BR": "amazon.com.br",
            "MX": "amazon.com.mx",
            "IT": "amazon.it",
            "ES": "amazon.es",
            "NL": "amazon.nl"
        }
        
        # Country-specific popular e-commerce sites
        self.local_sites = {
            "US": ["walmart", "bestbuy", "target", "newegg", "bhphotovideo"],
            "IN": ["flipkart", "snapdeal", "myntra", "nykaa", "bigbasket"],
            "UK": ["argos", "currys", "johnlewis", "very", "ao"],
            "CA": ["canadiantire", "bestbuy.ca", "thebay"],
            "AU": ["jbhifi", "harveynorman", "bigw", "kmart"],
            "DE": ["otto", "zalando", "mediamarkt", "saturn"],
            "FR": ["fnac", "darty", "cdiscount", "laredoute"],
            "JP": ["rakuten", "yodobashi", "bic-camera"],
            "BR": ["mercadolivre", "americanas", "submarino"],
            "MX": ["mercadolibre", "liverpool", "palacio"],
            "IT": ["eprice", "unieuro", "mediaworld"],
            "ES": ["elcorteingles", "pccomponentes", "mediamarkt"],
            "NL": ["bol", "coolblue", "mediamarkt"]
        }
    
    async def search_all_sources(self, query: str, country: str) -> Dict[str, Dict]:
        """
        Search all available sources for a product
        
        What this does: Orchestrates searches across multiple platforms simultaneously
        Why: Maximizes product coverage and price comparison options
        Returns: Dictionary with results from each source
        """
        logger.info(f"Starting comprehensive search for '{query}' in {country}")
        
        # Create search tasks for concurrent execution
        search_tasks = []
        
        # 1. Google Shopping (primary source - best structured data)
        search_tasks.append(
            ("google_shopping", self.search_google_shopping(query, country))
        )
        
        # 2. Amazon (if available in country)
        if country in self.amazon_domains:
            search_tasks.append(
                ("amazon", self.search_amazon(query, country))
            )
        
        # 3. Google general search for local sites
        search_tasks.append(
            ("google_general", self.search_google_with_local_sites(query, country))
        )
        
        # 4. eBay (global marketplace)
        search_tasks.append(
            ("ebay", self.search_ebay(query, country))
        )
        
        # Execute all searches concurrently
        logger.info(f"Executing {len(search_tasks)} concurrent searches...")
        
        results = {}
        search_futures = [task[1] for task in search_tasks]
        search_names = [task[0] for task in search_tasks]
        
        try:
            # Wait for all searches to complete (with timeout)
            completed_results = await asyncio.wait_for(
                asyncio.gather(*search_futures, return_exceptions=True),
                timeout=30.0  # 30 second timeout for all searches
            )
            
            # Process results
            for name, result in zip(search_names, completed_results):
                if isinstance(result, Exception):
                    logger.error(f"{name} search failed: {str(result)}")
                    results[name] = {"error": str(result)}
                else:
                    results[name] = result
                    logger.info(f"{name} search completed successfully")
            
        except asyncio.TimeoutError:
            logger.error("Search timeout - some sources may be slow")
            results["timeout_error"] = "Some searches timed out"
        
        logger.info(f"Comprehensive search completed. Sources: {list(results.keys())}")
        return results
    
    async def search_google_shopping(self, query: str, country: str) -> Dict:
        """Enhanced Google Shopping search with better parameters"""
        try:
            search_params = {
                "engine": "google_shopping",
                "q": query,
                "gl": country.lower(),  # Country code
                "hl": "en",  # Language
                "api_key": self.api_key,
                "num": 30,  # More results for better coverage
                "no_cache": True, # Get fresh results
                "sort_by": "price_low_to_high"  # Price sorting
            }
            
            logger.info(f"Starting Google Shopping search: {query} in {country}")
            
            # SerpAPI is synchronous, so we run it in a thread pool
            loop = asyncio.get_event_loop()
            search = GoogleSearch(search_params)
            result = await loop.run_in_executor(None, search.get_dict)
            
            if "error" in result:
                logger.error(f"[SERP API] Google Shopping error: {result['error']}")
                return {"error": result["error"]}
            

            # Extract and count results
            shopping_results = result.get('shopping_results', [])
            logger.info(f"Google Shopping: Found {len(shopping_results)} products")
            
            return result
            
        except Exception as e:
            logger.error(f"[SERP API] Google Shopping search failed: {str(e)}")
            return {"error": str(e)}
    
    async def search_amazon(self, query: str, country: str) -> Dict:
        """Enhanced Amazon search via SerpAPI"""
        try:
            domain = self.amazon_domains.get(country, "amazon.com")
            
            search_params = {
                "engine": "amazon",
                "amazon_domain": domain,
                "q": query,
                "api_key": self.api_key,
                "no_cache": True
            }
            
            logger.info(f"Starting Amazon search: {query} on {domain}")
            
            loop = asyncio.get_event_loop()
            search = GoogleSearch(search_params)
            result = await loop.run_in_executor(None, search.get_dict)
            
            if "error" in result:
                logger.error(f"[SERP API] Amazon search error: {result['error']}")
                return {"error": result["error"]}
            
            # Extract and count results
            organic_results = result.get('organic_results', [])
            logger.info(f"Amazon: Found {len(organic_results)} products")
            
            return result
            
        except Exception as e:
            logger.error(f"Amazon search failed: {str(e)}")
            return {"error": str(e)}
    
    async def search_google_with_local_sites(self, query: str, country: str) -> Dict:
        """Search Google with focus on local e-commerce sites"""
        try:
            # Get local sites for the country
            local_sites = self.local_sites.get(country, [])
            sites_query = " OR ".join([f"site:{site}" for site in local_sites[:5]])  # Limit to top 5
            
            # Enhanced query to find local e-commerce results
            enhanced_query = f"{query} buy online price ({sites_query})"
            
            search_params = {
                "engine": "google",
                "q": enhanced_query,
                "gl": country.lower(),
                "hl": "en",
                "api_key": self.api_key,
                "num": 20,
                "no_cache": True
            }
            
            logger.info(f"Google local sites search: {enhanced_query}")
            
            loop = asyncio.get_event_loop()
            search = GoogleSearch(search_params)
            result = await loop.run_in_executor(None, search.get_dict)
            
            if "error" in result:
                logger.error(f"Google local search error: {result['error']}")
                return {"error": result["error"]}
            
            logger.info(f"Google general search completed: {len(result.get('organic_results', []))} results")
            return result
            
        except Exception as e:
            logger.error(f"Google local sites search failed: {str(e)}")
            return {"error": str(e)}
    
    async def search_ebay(self, query: str, country: str) -> Dict:
        """Search eBay for additional product options"""
        try:
            # eBay domain mapping
            ebay_domains = {
                "US": "ebay.com",
                "UK": "ebay.co.uk", 
                "CA": "ebay.ca",
                "AU": "ebay.com.au",
                "DE": "ebay.de",
                "FR": "ebay.fr",
                "IT": "ebay.it",
                "ES": "ebay.es"
            }
            
            domain = ebay_domains.get(country, "ebay.com")
            
            search_params = {
                "engine": "ebay",
                "ebay_domain": domain,
                "q": query,
                "api_key": self.api_key,
                "no_cache": True
            }
            
            logger.info(f"eBay search: {query} on {domain}")
            
            loop = asyncio.get_event_loop()
            search = GoogleSearch(search_params)
            result = await loop.run_in_executor(None, search.get_dict)
            
            if "error" in result:
                logger.error(f"eBay search error: {result['error']}")
                return {"error": result["error"]}
            
            organic_results = result.get('organic_results', [])
            logger.info(f"eBay: Found {len(organic_results)} products")
            
            return result
            
        except Exception as e:
            logger.error(f"eBay search failed: {str(e)}")
            return {"error": str(e)}
    
    async def test_connection(self) -> Dict:
        """Enhanced connection test"""
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
            
            account_info = result.get("search_metadata", {})
            
            return {
                "connected": True,
                "message": "SerpAPI connection successful",
                "account_info": {
                    "id": account_info.get("id"),
                    "status": account_info.get("status"),
                    "total_time_taken": account_info.get("total_time_taken")
                }
            }
            
        except Exception as e:
            logger.error(f"SerpAPI connection test failed: {str(e)}")
            return {
                "connected": False,
                "error": str(e),
                "message": "SerpAPI connection test failed"
            }