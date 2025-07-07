import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SearchErrorHandler:
    """
    Handles errors and provides fallback mechanisms for search operations
    
    What this does: Manages API failures, timeouts, and data quality issues
    Why: Real-world APIs fail - we need graceful degradation
    """
    
    def __init__(self):
        self.error_counts = {}
        self.last_errors = {}
    
    def handle_source_error(self, source_name: str, error: Exception) -> Dict[str, Any]:
        """Handle errors from individual search sources"""
        error_msg = str(error)
        
        # Track error frequency
        self.error_counts[source_name] = self.error_counts.get(source_name, 0) + 1
        self.last_errors[source_name] = {
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "count": self.error_counts[source_name]
        }
        
        logger.warning(f"Source {source_name} failed: {error_msg}")
        
        return {
            "error": error_msg,
            "source": source_name,
            "timestamp": datetime.now().isoformat(),
            "retry_suggested": self.error_counts[source_name] < 3
        }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered"""
        return {
            "total_sources_with_errors": len(self.error_counts),
            "error_counts": self.error_counts,
            "last_errors": self.last_errors
        }