from typing import Dict, Any

class MetricsService:
    """
    Service responsible for monitoring and calculating business operational metrics:
    - Total number of processed queries.
    - Responses served from cache (cache hits).
    - Number of queries escalated to advisor via WhatsApp.
    - Escalation rate (%) and cache success rate (%).
    - Estimated costs ($ USD).
    """

    def __init__(self):
        self.total_queries: int = 0
        self.cached_queries: int = 0
        self.escalated_queries: int = 0
        self.total_tokens_estimated: int = 0

    def record_query(self, is_cached: bool = False, is_escalated: bool = False, tokens: int = 250) -> None:
        """
        Records a new interaction processed by the backend.
        """
        self.total_queries += 1
        if is_cached:
            self.cached_queries += 1
        if is_escalated:
            self.escalated_queries += 1
        self.total_tokens_estimated += tokens

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Returns a structured summary of all accumulated metrics.
        """
        escalation_rate = (
            round((self.escalated_queries / self.total_queries) * 100, 2)
            if self.total_queries > 0 else 0.0
        )
        cache_hit_rate = (
            round((self.cached_queries / self.total_queries) * 100, 2)
            if self.total_queries > 0 else 0.0
        )
        
        # Groq Llama 3.3 70B model is 100% free in its official inference tier
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

# Global metrics service instance
metrics_service = MetricsService()
