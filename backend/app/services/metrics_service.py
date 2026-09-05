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
        self.total_tokens: int = 0

    @property
    def total_tokens_estimated(self) -> int:
        return self.total_tokens

    @total_tokens_estimated.setter
    def total_tokens_estimated(self, value: int):
        self.total_tokens = value

    def record_query(self, is_cached: bool = False, is_escalated: bool = False, tokens: int = 0) -> None:
        """
        Records a new interaction processed by the backend with actual token usage.
        """
        self.total_queries += 1
        if is_cached:
            self.cached_queries += 1
        if is_escalated:
            self.escalated_queries += 1
        self.total_tokens += max(0, tokens)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Returns a structured summary of all accumulated operational metrics.
        """
        escalation_rate = (
            round((self.escalated_queries / self.total_queries) * 100, 2)
            if self.total_queries > 0 else 0.0
        )
        cache_hit_rate = (
            round((self.cached_queries / self.total_queries) * 100, 2)
            if self.total_queries > 0 else 0.0
        )
        
        # Groq LPU inference tier cost tracking ($0.00 in free tier, or ~$0.00059 per 1K tokens standard rate)
        estimated_cost_usd = round((self.total_tokens / 1000.0) * 0.00059, 4)

        return {
            "total_queries": self.total_queries,
            "cached_queries": self.cached_queries,
            "escalated_queries": self.escalated_queries,
            "escalation_rate_percentage": f"{escalation_rate}%",
            "cache_hit_rate_percentage": f"{cache_hit_rate}%",
            "total_tokens": self.total_tokens,
            "total_tokens_estimated": self.total_tokens,
            "estimated_cost_usd": f"${estimated_cost_usd:.4f} USD (Groq LPU Tier)"
        }

# Global metrics service instance
metrics_service = MetricsService()
