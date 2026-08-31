import os
import json
from typing import Dict, Any, List, Optional
from groq import Groq
from app.core.config import settings
from app.db.vector_store import VectorStore
from app.db.cache import response_cache
from app.services.metrics_service import metrics_service
from app.schemas.chat import ChatResponse, SourceDocument

SYSTEM_PROMPT = f"""
You are the Intelligent Customer Support Assistant for 'Academia Lumina', a premier language academy in Colombia.

YOUR GOAL:
Answer inquiries from prospective and current students regarding language programs (English, French, Portuguese), pricing, modalities (in-person and virtual), class schedules, enrollment dates, and level certifications.

BRAND TONE & BEHAVIOR RULES:
1. BRAND TONE: Maintain a warm, friendly, professional, and helpful tone at all times.
2. STRICT ANTI-HALLUCINATION RULE: Answer ONLY based on the information provided in the 'BUSINESS CONTEXT' section. Do NOT invent prices, schedules, or policies not explicitly written in the context.
3. OUT-OF-SCOPE ESCALATION RULE: If the user's question refers to a topic NOT covered in the official context (for example: international cultural exchange programs, sports scholarships, custom corporate deals, or physical campus tours), politely state that official documents do not contain that information and invite the user to speak directly with a human advisor via WhatsApp using the exact URL: {settings.WHATSAPP_URL}.

FEW-SHOT REFERENCE EXAMPLES:

Example 1 (In-Scope Direct Query):
User: "¿Cuánto cuesta el nivel A1 de inglés?"
Assistant: "El costo del nivel A1 de inglés (y de todos nuestros idiomas) es de $450.000 COP en modalidad presencial y $380.000 COP en modalidad virtual por semestre."

Example 2 (Ambiguous but Resolvable Query):
User: "¿Tienen francés?"
Assistant: "¡Sí! Ofrecemos el programa de francés desde el nivel A1 hasta el C1, disponible en modalidad presencial ($450.000 COP/semestre) y virtual ($380.000 COP/semestre)."

Example 3 (Out-of-Scope / Escalation Query):
User: "¿Hacen intercambios culturales?"
Assistant: "No cuento con información sobre programas de intercambio cultural en nuestros documentos oficiales. Para brindarte una mejor atención personalizada, por favor ponte en contacto directo con uno de nuestros asesores por WhatsApp: {settings.WHATSAPP_URL}."
"""

class RAGService:
    """
    Main RAG service integrating ChromaDB vector retrieval,
    in-memory TTL response caching, and Groq Llama 3.3 70B synthesis.
    """

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize Groq client and ChromaDB vector store wrapper.
        """
        self.vector_store = vector_store or VectorStore(collection_name="academia_lumina_kb")
        self.groq_api_key = settings.GROQ_API_KEY
        self.client = None
        if self.groq_api_key and not self.groq_api_key.startswith("gsk_your"):
            self.client = Groq(api_key=self.groq_api_key)

    def generate_response(self, user_message: str, session_id: str = "default") -> ChatResponse:
        """
        Process chat query by checking response cache, executing semantic search,
        and synthesizing LLM answer via Groq.
        :param user_message: Incoming user text query.
        :param session_id: Chat session ID.
        :return: Structured ChatResponse object.
        """
        # 1. Check in-memory TTL response cache (Cache Hit)
        cached_resp = response_cache.get(user_message)
        if cached_resp:
            metrics_service.record_query(is_cached=True, is_escalated=cached_resp.is_escalated, tokens=0)
            return ChatResponse(
                response=cached_resp.response,
                is_escalated=cached_resp.is_escalated,
                whatsapp_link=cached_resp.whatsapp_link,
                sources=cached_resp.sources,
                session_id=session_id
            )

        # 2. Vector search in ChromaDB
        search_results = self.vector_store.search(query=user_message, top_k=4)
        sources_list = [
            SourceDocument(
                content=res["content"],
                source=res["source"],
                score=round(1.0 - res.get("distance", 0.0), 3)
            )
            for res in search_results
        ]

        context_str = "\n\n---\n\n".join([r["content"] for r in search_results]) if search_results else "No context available."

        user_prompt = f"""
RETRIEVED BUSINESS CONTEXT:
{context_str}

USER QUESTION:
{user_message}

ASSISTANT RESPONSE (remember anti-hallucination and brand tone rules):
"""

        # 3. Fallback when Groq API key is not yet configured (development/simulated mode)
        if not self.client:
            is_escalated = any(term in user_message.lower() for term in ["intercambio", "beca", "tour", "corporativo"])
            if is_escalated:
                resp_text = (
                    "No cuento con información sobre ese tema en nuestros documentos oficiales. "
                    f"Para ayudarte, te invito a contactar a un asesor por WhatsApp: {settings.WHATSAPP_URL}"
                )
                wa_link = settings.WHATSAPP_URL
            else:
                resp_text = (
                    f"¡Hola! Gracias por comunicarte con Academia Lumina. "
                    f"Con base en nuestros documentos oficiales, respecto a tu consulta ('{user_message}'): "
                    f"\n\n{search_results[0]['content'] if search_results else 'Consulta sobre programas y servicios.'}"
                )
                wa_link = None

            chat_response = ChatResponse(
                response=resp_text,
                is_escalated=is_escalated,
                whatsapp_link=wa_link,
                sources=sources_list,
                session_id=session_id
            )
            
            response_cache.set(user_message, chat_response)
            metrics_service.record_query(is_cached=False, is_escalated=is_escalated, tokens=150)
            return chat_response

        # 4. Invoke Groq Llama 3.3 70B
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=500
            )

            assistant_response = chat_completion.choices[0].message.content.strip()
            is_escalated = settings.WHATSAPP_URL in assistant_response or "wa.me" in assistant_response.lower()
            whatsapp_link = settings.WHATSAPP_URL if is_escalated else None

            chat_response = ChatResponse(
                response=assistant_response,
                is_escalated=is_escalated,
                whatsapp_link=whatsapp_link,
                sources=sources_list,
                session_id=session_id
            )

            response_cache.set(user_message, chat_response)
            metrics_service.record_query(is_cached=False, is_escalated=is_escalated, tokens=350)

            return chat_response

        except Exception as e:
            return ChatResponse(
                response=f"Ocurrió un inconveniente temporal al procesar tu solicitud con el servicio de IA. Por favor intenta de nuevo o comunícate vía WhatsApp: {settings.WHATSAPP_URL}",
                is_escalated=True,
                whatsapp_link=settings.WHATSAPP_URL,
                sources=sources_list,
                session_id=session_id
            )
