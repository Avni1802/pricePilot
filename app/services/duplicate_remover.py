import logging
from typing import List, Dict, Set, Optional  # Add Optional here
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class DuplicateRemover:
    """
    Intelligently removes duplicate products from search results
    
    What this does:
    - Identifies duplicate products across different websites
    - Keeps the best version of each product
    - Uses fuzzy matching for product names
    - Considers price similarity
    
    Why: Same products appear on multiple sites, creating noise
    How: Compares product names, prices, and other attributes
    """
    
    def __init__(self):
        # Similarity thresholds
        self.name_similarity_threshold = 0.8  # 80% similar names = duplicate
        self.price_similarity_threshold = 0.15  # 15% price difference = similar
        
        # Website priority (higher = better source)
        self.website_priority = {
            "apple": 10,
            "amazon": 9,
            "bestbuy": 8,
            "walmart": 7,
            "target": 6,
            "ebay": 5,
            "flipkart": 8,  # High priority in India
            "myntra": 7,
            "snapdeal": 6,
            "argos": 7,     # UK
            "currys": 6,
            "very": 5,
            "default": 3
        }
    
    def remove_duplicates(self, products: List[Dict]) -> List[Dict]:
        """
        Remove duplicate products and keep the best version of each
        
        What this does: Finds similar products and keeps only the best one
        Why: Reduces noise and improves user experience
        Returns: List of unique products
        """
        if not products:
            return []
        
        logger.info(f"🔍 Starting duplicate removal for {len(products)} products")
        
        # Step 1: Group similar products
        product_groups = self._group_similar_products(products)
        
        # Step 2: Select best product from each group
        unique_products = []
        for group in product_groups:
            best_product = self._select_best_product(group)
            unique_products.append(best_product)
        
        logger.info(f"✅ Duplicate removal complete: {len(unique_products)} unique products")
        
        return unique_products
    
    def _group_similar_products(self, products: List[Dict]) -> List[List[Dict]]:
        """Group products that are likely duplicates"""
        groups = []
        used_indices = set()
        
        for i, product1 in enumerate(products):
            if i in used_indices:
                continue
            
            # Start a new group with this product
            current_group = [product1]
            used_indices.add(i)
            
            # Find similar products
            for j, product2 in enumerate(products):
                if j <= i or j in used_indices:
                    continue
                
                if self._are_products_similar(product1, product2):
                    current_group.append(product2)
                    used_indices.add(j)
            
            groups.append(current_group)
        
        logger.debug(f"Grouped {len(products)} products into {len(groups)} groups")
        return groups
    
    def _are_products_similar(self, product1: Dict, product2: Dict) -> bool:
        """Determine if two products are likely duplicates"""
        
        # Compare product names
        name1 = self._normalize_product_name(product1.get("productName", ""))
        name2 = self._normalize_product_name(product2.get("productName", ""))
        
        if not name1 or not name2:
            return False
        
        name_similarity = SequenceMatcher(None, name1, name2).ratio()
        
        # If names are very similar, check prices
        if name_similarity >= self.name_similarity_threshold:
            price1 = self._extract_numeric_price(product1.get("price", ""))
            price2 = self._extract_numeric_price(product2.get("price", ""))
            
            if price1 and price2:
                # Calculate price difference percentage
                price_diff = abs(price1 - price2) / max(price1, price2)
                
                # Similar names + similar prices = duplicate
                if price_diff <= self.price_similarity_threshold:
                    return True
            
            # Similar names but no price info = likely duplicate
            elif not price1 and not price2:
                return name_similarity >= 0.9  # Higher threshold without price
        
        return False
    
    def _normalize_product_name(self, name: str) -> str:
        """Normalize product name for comparison"""
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common noise words
        noise_words = [
            "buy", "online", "shop", "store", "official", "genuine", "original",
            "free shipping", "fast delivery", "best price", "sale", "offer",
            "deal", "discount", "new", "latest", "2024", "2023"
        ]
        
        for noise in noise_words:
            normalized = normalized.replace(noise, "")
        
        # Remove extra whitespace and special characters
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _extract_numeric_price(self, price_str: str) -> Optional[float]:
        """Extract numeric price value"""
        if not price_str:
            return None
        
        try:
            # Remove commas and convert to float
            clean_price = str(price_str).replace(',', '')
            return float(clean_price)
        except (ValueError, TypeError):
            return None
    
    def _select_best_product(self, product_group: List[Dict]) -> Dict:
        """Select the best product from a group of duplicates"""
        if len(product_group) == 1:
            return product_group[0]
        
        # Score each product
        scored_products = []
        for product in product_group:
            score = self._calculate_product_score(product)
            scored_products.append((score, product))
        
        # Sort by score (highest first) and return the best
        scored_products.sort(key=lambda x: x[0], reverse=True)
        best_product = scored_products[0][1]
        
        # Add metadata about duplicate removal
        best_product = best_product.copy()
        best_product["duplicate_info"] = {
            "total_duplicates_found": len(product_group),
            "sources_merged": list(set(p.get("website", "Unknown") for p in product_group)),
            "price_range": {
                "min": min(self._extract_numeric_price(p.get("price", "0")) or 0 for p in product_group),
                "max": max(self._extract_numeric_price(p.get("price", "0")) or 0 for p in product_group)
            }
        }
        
        logger.debug(f"Selected best product from {len(product_group)} duplicates: {best_product.get('productName', 'Unknown')}")
        
        return best_product
    
    def _calculate_product_score(self, product: Dict) -> float:
        """Calculate a quality score for a product"""
        score = 0.0
        
        # Website priority score (0-10)
        website = product.get("website", "").lower()
        website_score = self.website_priority.get(website, self.website_priority["default"])
        score += website_score
        
        # AI validation score (0-10)
        if product.get("ai_validated", False):
            ai_score = (product.get("ai_confidence_score", 0) / 100) * 10
            score += ai_score
        
        # Data completeness score (0-5)
        completeness_score = 0
        if product.get("productName"):
            completeness_score += 1
        if product.get("price"):
            completeness_score += 1
        if product.get("link") and product["link"].startswith("http"):
            completeness_score += 1
        if product.get("image_url"):
            completeness_score += 1
        if product.get("rating"):
            completeness_score += 1
        
        score += completeness_score
        
        # Price availability bonus (0-2)
        if product.get("price") and self._extract_numeric_price(product["price"]):
            score += 2
        
        # Penalize obvious spam/low quality
        product_name = product.get("productName", "").lower()
        if any(spam_word in product_name for spam_word in ["click here", "buy now", "limited time"]):
            score -= 5
        
        return score
