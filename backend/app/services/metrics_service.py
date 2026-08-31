from typing import Dict, Any

class MetricsService:
    """
    Servicio encargado de monitorear y calcular métricas operativas del negocio:
    - Cantidad total de consultas atendidas.
    - Respuestas servidas desde la caché (cache hits).
    - Cantidad de consultas escaladas a asesor por WhatsApp.
    - Tasa de escalamiento (%) y tasa de éxito de la caché (%).
    - Estimación de costos ($ USD).
    """

    def __init__(self):
        self.total_queries: int = 0
        self.cached_queries: int = 0
        self.escalated_queries: int = 0
        self.total_tokens_estimated: int = 0

    def record_query(self, is_cached: bool = False, is_escalated: bool = False, tokens: int = 250) -> None:
        """
        Registra una nueva interacción procesada por el backend.
        """
        self.total_queries += 1
        if is_cached:
            self.cached_queries += 1
        if is_escalated:
            self.escalated_queries += 1
        self.total_tokens_estimated += tokens

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Retorna un resumen estructurado de todas las métricas acumuladas.
        """
        escalation_rate = (
            round((self.escalated_queries / self.total_queries) * 100, 2)
            if self.total_queries > 0 else 0.0
        )
        cache_hit_rate = (
            round((self.cached_queries / self.total_queries) * 100, 2)
            if self.total_queries > 0 else 0.0
        )
        
        # El modelo Groq Llama 3.3 70B es 100% gratuito en su nivel de inferencia oficial
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

# Instancia global del servicio de métricas
metrics_service = MetricsService()
