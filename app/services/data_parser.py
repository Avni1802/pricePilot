import re
from typing import List, Dict, Optional
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ProductDataParser:
    """Enhanced parser with better error handling and Amazon/eBay support"""
    
    def __init__(self):
        self.currency_codes = {
            'US': 'USD', 'CA': 'CAD', 'AU': 'AUD',
            'UK': 'GBP', 'IN': 'INR', 'JP': 'JPY',
            'DE': 'EUR', 'FR': 'EUR', 'IT': 'EUR', 'ES': 'EUR', 'NL': 'EUR',
            'BR': 'BRL', 'MX': 'MXN'
        }
    
    def parse_all_results(self, raw_results: Dict[str, Dict], country: str) -> List[Dict]:
        """Parse results from all sources with better error handling"""
        all_products = []
        
        logger.info(f"Parsing results from {len(raw_results)} sources")
        
        for source_name, source_data in raw_results.items():
            if "error" in source_data:
                logger.warning(f"Skipping {source_name}: {source_data['error']}")
                continue
            
            try:
                if source_name == "google_shopping":
                    products = self.parse_google_shopping(source_data, country)
                elif source_name == "amazon":
                    products = self.parse_amazon_enhanced(source_data, country)
                elif source_name == "google_general":
                    products = self.parse_google_general(source_data, country)
                elif source_name == "ebay":
                    products = self.parse_ebay_enhanced(source_data, country)
                else:
                    logger.warning(f"Unknown source: {source_name}")
                    continue
                
                logger.info(f"Parsed {len(products)} products from {source_name}")
                all_products.extend(products)
                
            except Exception as e:
                logger.error(f"Error parsing {source_name}: {str(e)}")
                continue
        
        # Remove duplicates based on similar product names and prices
        unique_products = self.remove_duplicates(all_products)
        logger.info(f"📦 Total unique products: {len(unique_products)}")
        
        return unique_products
    
    def parse_google_shopping(self, data: Dict, country: str) -> List[Dict]:
        """Parse Google Shopping results"""
        products = []
        shopping_results = data.get('shopping_results', [])
        
        for item in shopping_results:
            try:
                price_info = self.extract_price(item.get('price', ''), country)
                
                if not price_info['price']:
                    continue
                
                product = {
                    "link": item.get('link', ''),
                    "price": price_info['price'],
                    "currency": price_info['currency'],
                    "productName": item.get('title', ''),
                    "website": self.extract_website_name(item.get('source', '')),
                    "rating": str(item.get('rating', '')),
                    "availability": "In Stock",
                    "image_url": item.get('thumbnail', '')
                }
                
                if self.is_valid_product(product):
                    products.append(product)
                    
            except Exception as e:
                logger.debug(f"Skipping Google Shopping item: {str(e)}")
                continue
        
        return products
    
    def parse_amazon_enhanced(self, data: Dict, country: str) -> List[Dict]:
        """Enhanced Amazon parser with multiple result formats"""
        products = []
        
        # Try different result fields that Amazon might use
        results = (
            data.get('organic_results', []) or 
            data.get('products', []) or
            data.get('search_results', [])
        )
        
        logger.info(f"Amazon parser: Processing {len(results)} items")
        
        for item in results:
            try:
                # Try multiple price fields Amazon might use
                price_text = (
                    item.get('price', '') or 
                    item.get('price_string', '') or
                    item.get('price_upper', '') or
                    item.get('price_lower', '') or
                    item.get('price_range', '') or
                    str(item.get('price_symbol', '')) + str(item.get('price_value', ''))
                )
                
                price_info = self.extract_price(str(price_text), country)
                
                if not price_info['price']:
                    # Try extracting price from title or snippet
                    title_text = item.get('title', '')
                    snippet_text = item.get('snippet', '')
                    combined_text = f"{title_text} {snippet_text}"
                    price_info = self.extract_price(combined_text, country)
                
                if not price_info['price']:
                    continue
                
                # Get product title
                title = (
                    item.get('title', '') or 
                    item.get('name', '') or
                    item.get('product_name', '')
                )
                
                product = {
                    "link": item.get('link', ''),
                    "price": price_info['price'],
                    "currency": price_info['currency'],
                    "productName": self.clean_product_name(title),
                    "website": "Amazon",
                    "rating": str(item.get('rating', '') or item.get('reviews', {}).get('rating', '')),
                    "availability": item.get('availability', 'Available'),
                    "image_url": item.get('image', '') or item.get('thumbnail', '')
                }
                
                if self.is_valid_product(product):
                    products.append(product)
                    
            except Exception as e:
                logger.debug(f"Skipping Amazon item: {str(e)}")
                continue
        
        logger.info(f"Amazon parser: Successfully parsed {len(products)} products")
        return products
    
    def parse_google_general(self, data: Dict, country: str) -> List[Dict]:
        """Parse Google general search results"""
        products = []
        organic_results = data.get('organic_results', [])
        
        for item in organic_results:
            try:
                title = item.get('title', '')
                snippet = item.get('snippet', '')
                
                # Look for price in title or snippet
                price_text = f"{title} {snippet}"
                price_info = self.extract_price(price_text, country)
                
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
                    "rating": "",
                    "availability": "Check Website",
                    "image_url": ""
                }
                
                if self.is_valid_product(product):
                    products.append(product)
                    
            except Exception as e:
                logger.debug(f"Skipping Google general item: {str(e)}")
                continue
        
        return products
    
    def parse_ebay_enhanced(self, data: Dict, country: str) -> List[Dict]:
        """Enhanced eBay parser with multiple result formats"""
        products = []
        
        # Try different result fields that eBay might use
        results = (
            data.get('organic_results', []) or
            data.get('search_results', []) or
            data.get('items', [])
        )
        
        logger.info(f"eBay parser: Processing {len(results)} items")
        
        for item in results:
            try:
                # Try multiple price fields eBay might use
                price_text = (
                    item.get('price', '') or
                    item.get('current_price', '') or
                    item.get('buy_it_now_price', '') or
                    item.get('starting_bid', '') or
                    str(item.get('price_value', ''))
                )
                
                price_info = self.extract_price(str(price_text), country)
                
                if not price_info['price']:
                    # Try extracting from title
                    title_text = item.get('title', '')
                    price_info = self.extract_price(title_text, country)
                
                if not price_info['price']:
                    continue
                
                # Get product title
                title = (
                    item.get('title', '') or
                    item.get('name', '') or
                    item.get('listing_title', '')
                )
                
                # Determine availability/auction type
                availability = "Buy Now"
                if item.get('auction', False) or 'bid' in str(item.get('price', '')).lower():
                    availability = "Auction"
                elif item.get('buy_it_now', False):
                    availability = "Buy It Now"
                
                product = {
                    "link": item.get('link', ''),
                    "price": price_info['price'],
                    "currency": price_info['currency'],
                    "productName": self.clean_product_name(title),
                    "website": "eBay",
                    "rating": str(item.get('rating', '') or item.get('seller_rating', '')),
                    "availability": availability,
                    "image_url": item.get('thumbnail', '') or item.get('image', '')
                }
                
                if self.is_valid_product(product):
                    products.append(product)
                    
            except Exception as e:
                logger.debug(f"Skipping eBay item: {str(e)}")
                continue
        
        logger.info(f"eBay parser: Successfully parsed {len(products)} products")
        return products
    
    def extract_price(self, price_text: str, country: str) -> Dict[str, str]:
        """Enhanced price extraction with better patterns"""
        if not price_text:
            return {"price": "", "currency": ""}
        
        # Convert to string and clean
        price_text = str(price_text).strip()
        
        # Remove common noise
        clean_text = re.sub(r'(from|starting|as low as|up to|save|off|free shipping)', '', price_text.lower())
        
        # Enhanced price patterns - more comprehensive
        price_patterns = [
            r'[\$£€¥₹]\s*([0-9,]+\.?[0-9]*)',  # Symbol first: $999.99
            r'([0-9,]+\.?[0-9]*)\s*[\$£€¥₹]',  # Symbol last: 999.99$
            r'([0-9,]+\.?[0-9]*)\s*(USD|EUR|GBP|INR|JPY|CAD|AUD|BRL|MXN)',  # With currency code
            r'Price:\s*[\$£€¥₹]?\s*([0-9,]+\.?[0-9]*)',  # "Price: $999"
            r'([0-9,]+\.?[0-9]*)\s*dollars?',  # "999 dollars"
            r'([0-9,]+\.?[0-9]*)\s*rupees?',   # "999 rupees"
            r'([0-9,]+\.?[0-9]*)',  # Just numbers (last resort)
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                price_num = match.group(1).replace(',', '')
                
                # Skip if price is too small (likely not a real price)
                try:
                    if float(price_num) < 1:
                        continue
                except ValueError:
                    continue
                
                # Determine currency
                currency = self.currency_codes.get(country, 'USD')
                
                # Override currency if symbol/code found in text
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
                elif 'USD' in price_text.upper():
                    currency = 'USD'
                elif 'EUR' in price_text.upper():
                    currency = 'EUR'
                elif 'GBP' in price_text.upper():
                    currency = 'GBP'
                elif 'INR' in price_text.upper():
                    currency = 'INR'
                
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
        
        # Remove common noise patterns
        noise_patterns = [
            r'\s*-\s*(Buy Online|Shop Now|Best Price|Free Shipping).*',
            r'\s*\|\s*.*',  # Remove everything after |
            r'\s*-\s*Amazon.*',
            r'\s*-\s*eBay.*'
        ]
        
        for pattern in noise_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        return name.strip()
    
    def is_valid_product(self, product: Dict) -> bool:
        """Validate if product has minimum required information"""
        return (
            product.get('link') and 
            product.get('productName') and 
            product.get('price') and
            len(product.get('productName', '')) > 3 and
            product.get('link').startswith('http')
        )
    
    def remove_duplicates(self, products: List[Dict]) -> List[Dict]:
        """Remove duplicate products based on name similarity and price"""
        if not products:
            return []
        
        unique_products = []
        seen_combinations = set()
        
        for product in products:
            # Create a key based on cleaned name and price
            name_key = re.sub(r'[^a-zA-Z0-9]', '', product.get('productName', '').lower())[:20]
            price_key = product.get('price', '')
            combination_key = f"{name_key}_{price_key}"
            
            if combination_key not in seen_combinations:
                seen_combinations.add(combination_key)
                unique_products.append(product)
        
        return unique_products