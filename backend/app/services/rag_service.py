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
Eres el Asistente Inteligente de Atención al Cliente de 'Academia Lumina', una reconocida academia de idiomas en Colombia.

TU OBJETIVO:
Responder las dudas de futuros y actuales estudiantes sobre programas de idiomas (inglés, francés, portugués), precios, modalidades (presencial y virtual), horarios, inscripciones y certificaciones.

REGLAS DE COMPORTAMIENTO Y TONO:
1. TONO DE MARCA: Sé siempre amigable, cercano, profesional y servicial.
2. REGLA ESTRICTA ANTI-ALUCINACIÓN: Responde ÚNICAMENTE basándote en la información proporcionada en la sección 'CONTEXTO DE NEGOCIO'. No inventes precios, horarios ni políticas que no estén explícitamente escritas en el contexto.
3. REGLA DE ESCALAMIENTO FUERA DE ALCANCE (OUT-OF-SCOPE): Si la pregunta del usuario se refiere a un tema NO cubierto en el contexto (por ejemplo: intercambios culturales al exterior, becas deportivas, convenios corporativos a medida o tours físicos), debes responder amablemente indicando que no posees esa información en los documentos oficiales e invitar al usuario a chatear con un asesor humano a través de WhatsApp mediante la URL exacta: {settings.WHATSAPP_URL}.

EJEMPLOS FEW-SHOT DE REFERENCIA:

Ejemplo 1 (Pregunta dentro de alcance):
Usuario: "¿Cuánto cuesta el nivel A1 de inglés?"
Asistente: "El costo del nivel A1 de inglés (y de todos nuestros idiomas) es de $450.000 COP en modalidad presencial y $380.000 COP en modalidad virtual por semestre."

Ejemplo 2 (Pregunta ambigua pero resoluble):
Usuario: "¿Tienen francés?"
Asistente: "¡Sí! Ofrecemos el programa de francés desde el nivel A1 hasta el C1, disponible en modalidad presencial ($450.000 COP/semestre) y virtual ($380.000 COP/semestre)."

Ejemplo 3 (Pregunta fuera de alcance / Escalamiento):
Usuario: "¿Hacen intercambios culturales?"
Asistente: "No cuento con información sobre programas de intercambio cultural en nuestros documentos oficiales. Para brindarte una mejor atención personalizada, por favor ponte en contacto directo con uno de nuestros asesores por WhatsApp: {settings.WHATSAPP_URL}."
"""

class RAGService:
    """
    Servicio principal de RAG que integra el VectorStore de ChromaDB,
    el sistema de caché TTL en memoria y la API del modelo Llama 3.3 70B de Groq.
    """

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Inicializa el cliente de Groq y el almacenamiento vectorial.
        """
        self.vector_store = vector_store or VectorStore(collection_name="academia_lumina_kb")
        self.groq_api_key = settings.GROQ_API_KEY
        self.client = None
        if self.groq_api_key and not self.groq_api_key.startswith("gsk_your"):
            self.client = Groq(api_key=self.groq_api_key)

    def generate_response(self, user_message: str, session_id: str = "default") -> ChatResponse:
        """
        Procesa una consulta verificando la caché, recuperando contexto vectorial 
        y generando la respuesta con Groq.
        :param user_message: Pregunta enviada por el usuario.
        :param session_id: ID de sesión de chat.
        :return: Objeto ChatResponse estructurado.
        """
        # 1. Comprobar si la respuesta está en caché (Cache Hit)
        cached_resp = response_cache.get(user_message)
        if cached_resp:
            # Retornar copia de caché ajustando la sesión actual
            metrics_service.record_query(is_cached=True, is_escalated=cached_resp.is_escalated, tokens=0)
            return ChatResponse(
                response=cached_resp.response,
                is_escalated=cached_resp.is_escalated,
                whatsapp_link=cached_resp.whatsapp_link,
                sources=cached_resp.sources,
                session_id=session_id
            )

        # 2. Búsqueda semántica en ChromaDB
        search_results = self.vector_store.search(query=user_message, top_k=4)
        sources_list = [
            SourceDocument(
                content=res["content"],
                source=res["source"],
                score=round(1.0 - res.get("distance", 0.0), 3)
            )
            for res in search_results
        ]

        context_str = "\n\n---\n\n".join([r["content"] for r in search_results]) if search_results else "No hay contexto disponible."

        user_prompt = f"""
CONTEXTO DE NEGOCIO RECUPERADO:
{context_str}

PREGUNTA DEL USUARIO:
{user_message}

RESPUESTA DEL ASISTENTE (recuerda seguir las reglas anti-alucinación y el tono de marca):
"""

        # 3. Si la API Key de Groq no está activa (modo desarrollo/simulado)
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
            
            # Guardar en caché y registrar métrica
            response_cache.set(user_message, chat_response)
            metrics_service.record_query(is_cached=False, is_escalated=is_escalated, tokens=150)
            return chat_response

        # 4. Invocación a Groq Llama 3.3 70B
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

            # Almacenar en caché para futuras consultas idénticas
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
