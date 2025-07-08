import logging
from typing import Dict, List, Any
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

class SearchErrorHandler:
    """
    Enhanced error handler for Phase 3 AI operations
    
    What this does: Tracks and handles errors across all search pipeline stages
    Why: Provides robust error handling and debugging information
    How: Collects errors from each stage and provides recovery strategies
    """
    
    def __init__(self):
        self.error_counts = {}
        self.last_errors = {}
        self.ai_error_counts = {}
        self.pipeline_stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "ai_validations": 0,
            "ai_failures": 0,
            "duplicate_removals": 0,
            "confidence_scorings": 0
        }
    
    def log_error(self, source: str, error: Exception, context: Dict = None):
        """Log an error with context"""
        error_msg = str(error)
        
        # Update error counts
        if source not in self.error_counts:
            self.error_counts[source] = 0
        self.error_counts[source] += 1
        
        # Store last error
        self.last_errors[source] = {
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            "traceback": traceback.format_exc() if logger.isEnabledFor(logging.DEBUG) else None
        }
        
        # Log the error
        logger.error(f"❌ {source} error: {error_msg}")
        if context:
            logger.debug(f"Context: {context}")
    
    def log_ai_error(self, ai_service: str, error: Exception, query: str = None):
        """Log AI-specific errors"""
        if ai_service not in self.ai_error_counts:
            self.ai_error_counts[ai_service] = 0
        self.ai_error_counts[ai_service] += 1
        
        context = {"query": query} if query else {}
        self.log_error(f"ai_{ai_service}", error, context)
        
        # Update AI stats
        self.pipeline_stats["ai_failures"] += 1
    
    def log_pipeline_stage(self, stage: str, success: bool, count: int = 0):
        """Log pipeline stage completion"""
        if success:
            logger.info(f"✅ {stage}: {count} items processed")
            
            # Update pipeline stats
            if stage == "search":
                self.pipeline_stats["total_searches"] += 1
                if success:
                    self.pipeline_stats["successful_searches"] += 1
            elif stage == "ai_validation":
                self.pipeline_stats["ai_validations"] += 1
            elif stage == "duplicate_removal":
                self.pipeline_stats["duplicate_removals"] += 1
            elif stage == "confidence_scoring":
                self.pipeline_stats["confidence_scorings"] += 1
        else:
            logger.error(f"❌ {stage}: Failed")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered"""
        return {
            "total_sources_with_errors": len(self.error_counts),
            "error_counts": self.error_counts,
            "ai_error_counts": self.ai_error_counts,
            "last_errors": self.last_errors,
            "pipeline_stats": self.pipeline_stats,
            "success_rate": self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> Dict[str, float]:
        """Calculate success rates for different operations"""
        total_searches = self.pipeline_stats["total_searches"]
        successful_searches = self.pipeline_stats["successful_searches"]
        ai_validations = self.pipeline_stats["ai_validations"]
        ai_failures = self.pipeline_stats["ai_failures"]
        
        return {
            "overall_search_success_rate": (successful_searches / max(total_searches, 1)) * 100,
            "ai_validation_success_rate": (ai_validations / max(ai_validations + ai_failures, 1)) * 100,
            "total_searches": total_searches,
            "successful_searches": successful_searches,
            "ai_operations": ai_validations + ai_failures
        }
    
    def should_fallback_to_basic_search(self) -> bool:
        """Determine if we should fallback to basic search due to AI failures"""
        ai_failure_rate = self.ai_error_counts.get("ai_validator", 0)
        return ai_failure_rate > 3  # Fallback after 3 AI failures
    
    def get_recovery_suggestions(self) -> List[str]:
        """Get suggestions for error recovery"""
        suggestions = []
        
        # Check for common error patterns
        if "serpapi" in self.error_counts:
            suggestions.append("Check SerpAPI key and quota limits")
        
        if "ai_validator" in self.ai_error_counts:
            suggestions.append("Check OpenAI API key and quota limits")
            suggestions.append("Consider using basic search as fallback")
        
        if self.pipeline_stats["total_searches"] > 0:
            success_rate = (self.pipeline_stats["successful_searches"] / self.pipeline_stats["total_searches"]) * 100
            if success_rate < 50:
                suggestions.append("High failure rate detected - check service configurations")
        
        return suggestions