import re
from typing import List, Dict, Optional
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ProductDataParser:
    """
    Parses raw search results into structured product data
    
    What this does: Converts messy API responses into clean ProductResult objects
    Why: Different sources have different data formats - we need consistency
    """
    
    def __init__(self):
        # Currency symbols for price extraction
        self.currency_symbols = {
            'US': '$', 'CA': 'C$', 'AU': 'A$',
            'UK': '£', 'IN': '₹', 'JP': '¥',
            'DE': '€', 'FR': '€', 'IT': '€', 'ES': '€', 'NL': '€',
            'BR': 'R$', 'MX': '$'
        }
        
        # Currency codes
        self.currency_codes = {
            'US': 'USD', 'CA': 'CAD', 'AU': 'AUD',
            'UK': 'GBP', 'IN': 'INR', 'JP': 'JPY',
            'DE': 'EUR', 'FR': 'EUR', 'IT': 'EUR', 'ES': 'EUR', 'NL': 'EUR',
            'BR': 'BRL', 'MX': 'MXN'
        }
    
    def parse_all_results(self, raw_results: Dict[str, Dict], country: str) -> List[Dict]:
        """
        Parse results from all sources into unified product list
        
        What this does: Takes raw API responses and converts them to our standard format
        Why: Each source (Google Shopping, Amazon, etc.) has different response formats
        Returns: List of dictionaries matching our ProductResult format
        """
        all_products = []
        
        logger.info(f"Starting to parse results from {len(raw_results)} sources")
        
        for source_name, source_data in raw_results.items():
            if "error" in source_data:
                logger.warning(f"Skipping {source_name} due to error: {source_data['error']}")
                continue
            
            try:
                if source_name == "google_shopping":
                    products = self.parse_google_shopping(source_data, country)
                elif source_name == "amazon":
                    products = self.parse_amazon(source_data, country)
                elif source_name == "google_general":
                    products = self.parse_google_general(source_data, country)
                elif source_name == "ebay":
                    products = self.parse_ebay(source_data, country)
                else:
                    logger.warning(f"Unknown source: {source_name}")
                    continue
                
                logger.info(f"Parsed {len(products)} products from {source_name}")
                all_products.extend(products)
                
            except Exception as e:
                logger.error(f"Error parsing {source_name}: {str(e)}")
                continue
        
        logger.info(f"Total products parsed: {len(all_products)}")
        return all_products
    
    def parse_google_shopping(self, data: Dict, country: str) -> List[Dict]:
        """Parse Google Shopping results"""
        products = []
        shopping_results = data.get('shopping_results', [])
        
        for item in shopping_results:
            try:
                # Extract price information
                price_info = self.extract_price(item.get('price', ''), country)
                
                # Skip if no valid price found
                if not price_info['price']:
                    continue
                
                product = {
                    "link": item.get('link', ''),
                    "price": price_info['price'],
                    "currency": price_info['currency'],
                    "productName": item.get('title', ''),
                    "website": self.extract_website_name(item.get('source', '')),
                    "rating": item.get('rating'),
                    "availability": "In Stock" if item.get('delivery') else None,
                    "image_url": item.get('thumbnail')
                }
                
                # Only add if we have essential information
                if product['link'] and product['productName'] and product['price']:
                    products.append(product)
                    
            except Exception as e:
                logger.error(f"Error parsing Google Shopping item: {str(e)}")
                continue
        
        return products
    
    def parse_amazon(self, data: Dict, country: str) -> List[Dict]:
        """Parse Amazon results"""
        products = []
        organic_results = data.get('organic_results', [])
        
        for item in organic_results:
            try:
                # Extract price from various possible fields
                price_text = (item.get('price', '') or 
                             item.get('price_string', '') or
                             item.get('price_upper', ''))
                
                price_info = self.extract_price(price_text, country)
                
                # Skip if no valid price
                if not price_info['price']:
                    continue
                
                product = {
                    "link": item.get('link', ''),
                    "price": price_info['price'],
                    "currency": price_info['currency'],
                    "productName": item.get('title', ''),
                    "website": "Amazon",
                    "rating": item.get('rating'),
                    "availability": "In Stock" if not item.get('is_prime_eligible') == False else "Check Availability",
                    "image_url": item.get('image')
                }
                
                if product['link'] and product['productName'] and product['price']:
                    products.append(product)
                    
            except Exception as e:
                logger.error(f"Error parsing Amazon item: {str(e)}")
                continue
        
        return products
    
    def parse_google_general(self, data: Dict, country: str) -> List[Dict]:
        """Parse Google general search results for e-commerce sites"""
        products = []
        organic_results = data.get('organic_results', [])
        
        for item in organic_results:
            try:
                # Look for price in title or snippet
                title = item.get('title', '')
                snippet = item.get('snippet', '')
                
                # Try to extract price from title or snippet
                price_text = f"{title} {snippet}"
                price_info = self.extract_price(price_text, country)
                
                # Skip if no price found
                if not price_info['price']:
                    continue
                
                # Extract website name from URL
                website_name = self.extract_website_name(item.get('link', ''))
                
                product = {
                    "link": item.get('link', ''),
                    "price": price_info['price'],
                    "currency": price_info['currency'],
                    "productName": self.clean_product_name(title),
                    "website": website_name,
                    "rating": None,
                    "availability": "Check Website",
                    "image_url": None
                }
                
                if product['link'] and product['productName'] and product['price']:
                    products.append(product)
                    
            except Exception as e:
                logger.error(f"Error parsing Google general item: {str(e)}")
                continue
        
        return products
    
    def parse_ebay(self, data: Dict, country: str) -> List[Dict]:
        """Parse eBay results"""
        products = []
        organic_results = data.get('organic_results', [])
        
        for item in organic_results:
            try:
                price_info = self.extract_price(item.get('price', ''), country)
                
                if not price_info['price']:
                    continue
                
                product = {
                    "link": item.get('link', ''),
                    "price": price_info['price'],
                    "currency": price_info['currency'],
                    "productName": item.get('title', ''),
                    "website": "eBay",
                    "rating": None,
                    "availability": "Auction/Buy Now",
                    "image_url": item.get('thumbnail')
                }
                
                if product['link'] and product['productName'] and product['price']:
                    products.append(product)
                    
            except Exception as e:
                logger.error(f"Error parsing eBay item: {str(e)}")
                continue
        
        return products
    
    def extract_price(self, price_text: str, country: str) -> Dict[str, str]:
        """
        Extract clean price and currency from text
        
        What this does: Finds price numbers in messy text and determines currency
        Why: Prices come in many formats: "$999", "999.99 USD", "₹75,000"
        Returns: {"price": "999.99", "currency": "USD"}
        """
        if not price_text:
            return {"price": "", "currency": ""}
        
        # Remove common non-price text
        clean_text = re.sub(r'(from|starting|as low as|up to|save|off)', '', price_text.lower())
        
        # Price patterns for different formats
        price_patterns = [
            r'[\$£€¥₹]\s*([0-9,]+\.?[0-9]*)',  # Symbol first: $999.99
            r'([0-9,]+\.?[0-9]*)\s*[\$£€¥₹]',  # Symbol last: 999.99$
            r'([0-9,]+\.?[0-9]*)\s*(USD|EUR|GBP|INR|JPY|CAD|AUD|BRL|MXN)',  # With currency code
            r'([0-9,]+\.?[0-9]*)',  # Just numbers
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, clean_text)
            if match:
                # Extract the numeric part
                price_num = match.group(1).replace(',', '')
                
                # Determine currency
                currency = self.currency_codes.get(country, 'USD')
                
                # Check if currency symbol/code was in the text
                if '$' in price_text:
                    currency = 'USD' if country == 'US' else self.currency_codes.get(country, 'USD')
                elif '£' in price_text:
                    currency = 'GBP'
                elif '€' in price_text:
                    currency = 'EUR'
                elif '₹' in price_text:
                    currency = 'INR'
                elif '¥' in price_text:
                    currency = 'JPY'
                elif any(code in price_text.upper() for code in ['USD', 'EUR', 'GBP', 'INR', 'JPY', 'CAD', 'AUD']):
                    for code in ['USD', 'EUR', 'GBP', 'INR', 'JPY', 'CAD', 'AUD', 'BRL', 'MXN']:
                        if code in price_text.upper():
                            currency = code
                            break
                
                return {"price": price_num, "currency": currency}
        
        return {"price": "", "currency": ""}
    
    def extract_website_name(self, url: str) -> str:
        """Extract clean website name from URL"""
        if not url:
            return "Unknown"
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. and common prefixes
            domain = re.sub(r'^(www\.|m\.)', '', domain)
            
            # Extract main domain name
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                main_domain = domain_parts[-2]
                return main_domain.capitalize()
            
            return domain.capitalize()
            
        except Exception:
            return "Unknown"
    
    def clean_product_name(self, name: str) -> str:
        """Clean and normalize product names"""
        if not name:
            return ""
        
        # Remove excessive whitespace
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Remove common noise words at the end
        noise_patterns = [
            r'\s*-\s*(Buy Online|Shop Now|Best Price|Free Shipping).*$',
            r'\s*\|\s*.*$',  # Remove everything after |
            r'\s*-\s*Amazon.*$',
            r'\s*-\s*eBay.*$'
        ]
        
        for pattern in noise_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        return name.strip()