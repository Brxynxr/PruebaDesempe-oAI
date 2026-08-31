from typing import Dict, Any

class MetricsService:
    """
    Service tracking and computing operational business metrics:
    - Total queries processed.
    - Queries served from cache (cache hits).
    - Queries escalated to human support via WhatsApp.
    - Escalation rate (%) and cache hit rate (%).
    - Estimated LLM inference cost ($ USD).
    """

    def __init__(self):
        self.total_queries: int = 0
        self.cached_queries: int = 0
        self.escalated_queries: int = 0
        self.total_tokens_estimated: int = 0

    def record_query(self, is_cached: bool = False, is_escalated: bool = False, tokens: int = 250) -> None:
        """
        Records a newly processed interaction metric.
        """
        self.total_queries += 1
        if is_cached:
            self.cached_queries += 1
        if is_escalated:
            self.escalated_queries += 1
        self.total_tokens_estimated += tokens

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Returns structured summary dictionary of operational metrics.
        """
        escalation_rate = (
            round((self.escalated_queries / self.total_queries) * 100, 2)
            if self.total_queries > 0 else 0.0
        )
        cache_hit_rate = (
            round((self.cached_queries / self.total_queries) * 100, 2)
            if self.total_queries > 0 else 0.0
        )
        
        # Groq Llama 3.3 70B inference is 100% free on official tier
        estimated_cost_usd = 0.0

        return {
            "total_queries": self.total_queries,
            "cached_queries": self.cached_queries,
            "escalated_queries": self.escalated_queries,
            "escalation_rate_percentage": f"{escalation_rate}%",
            "cache_hit_rate_percentage": f"{cache_hit_rate}%",
            "total_tokens_estimated": self.total_tokens_estimated,
            "estimated_cost_usd": f"${estimated_cost_usd:.4f} USD (Groq Free Tier)"
        }

# Global singleton metrics service instance
metrics_service = MetricsService()
