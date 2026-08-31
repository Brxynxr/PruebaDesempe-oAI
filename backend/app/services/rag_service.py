import os
import json
import re
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

REGLAS DE COMPORTAMIENTO, TONO Y ESTRUCTURA DE RESPUESTA:
1. TONO DE MARCA CORDIAL Y DIRECTO: Sé siempre amigable, cercano, profesional y servicial. Tu respuesta debe sonar fluida y humana, por ejemplo: "¡Hola! Gracias por comunicarte con Academia Lumina. Respecto a tu consulta sobre...".
2. RESPUESTAS CONCISAS Y CONCRETAS: Responde de forma directa al grano sin rodeos ni explicaciones excesivas. Integra la información de manera limpia sin pegar encabezados fríos de Markdown (como ## Título) ni fragmentos crudos.
3. REGLA ESTRICTA ANTI-ALUCINACIÓN: Responde ÚNICAMENTE basándote en la información proporcionada en la sección 'CONTEXTO DE NEGOCIO'. No inventes precios, horarios ni políticas que no estén explícitamente escritas en el contexto.
4. REGLA DE ESCALAMIENTO FUERA DE ALCANCE (OUT-OF-SCOPE): Si la pregunta del usuario se refiere a un tema NO cubierto en el contexto (por ejemplo: intercambios culturales al exterior, becas deportivas, convenios corporativos a medida o tours físicos), debes responder amablemente indicando que no posees esa información en los documentos oficiales e invitar al usuario a chatear con un asesor humano a través de WhatsApp mediante la URL exacta: {settings.WHATSAPP_URL}.

EJEMPLOS FEW-SHOT DE REFERENCIA:

Ejemplo 1 (Pregunta dentro de alcance):
Usuario: "¿Cuándo habilitan las inscripciones?"
Asistente: "¡Hola! Gracias por comunicarte con Academia Lumina. Respecto a tu consulta sobre inscripciones, se habilitan dos veces al año: para el primer semestre las inscripciones abren del 1 de noviembre al 20 de enero (inicio de clases en febrero), y para el segundo semestre del 1 de mayo al 20 de julio (inicio de clases en agosto), tanto para modalidad presencial como virtual."

Ejemplo 2 (Pregunta de precio directo):
Usuario: "¿Cuánto cuesta el nivel A1 de inglés?"
Asistente: "¡Hola! Gracias por escribirnos. El costo de cada nivel (incluyendo el nivel A1 de inglés) es de $450.000 COP en modalidad presencial y $380.000 COP en modalidad virtual por semestre."

Ejemplo 3 (Pregunta fuera de alcance / Escalamiento):
Usuario: "¿Hacen intercambios culturales a Canadá?"
Asistente: "¡Hola! No cuento con información sobre programas de intercambio cultural en nuestros documentos oficiales. Para brindarte una mejor atención personalizada, por favor ponte en contacto directo con uno de nuestros asesores por WhatsApp: {settings.WHATSAPP_URL}."
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

RESPUESTA DEL ASISTENTE (recuerda ser cordial, directo, natural y no pegar encabezados de Markdown):
"""

        # 3. Si la API Key de Groq no está activa (modo desarrollo/simulado)
        if not self.client:
            is_escalated = any(term in user_message.lower() for term in ["intercambio", "beca", "tour", "corporativo", "canadá", "exterior"])
            if is_escalated:
                resp_text = (
                    "¡Hola! No cuento con información sobre ese tema en nuestros documentos oficiales. "
                    f"Para brindarte una atención personalizada, te invito a chatear con un asesor por WhatsApp: {settings.WHATSAPP_URL}"
                )
                wa_link = settings.WHATSAPP_URL
            else:
                # Buscar entre los resultados recuperados el que mejor responda la consulta
                best_match = search_results[0]['content'] if search_results else 'Consulta sobre programas.'
                for res in search_results:
                    if any(word in res['content'].lower() for word in user_message.lower().split()):
                        best_match = res['content']
                        break

                clean_chunk = re.sub(r'^#{1,3}\s+.*\n?', '', best_match, flags=re.MULTILINE).strip()
                resp_text = (
                    f"¡Hola! Gracias por comunicarte con Academia Lumina. Respecto a tu consulta sobre '{user_message}':\n\n{clean_chunk}"
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

            response_cache.set(user_message, chat_response)
            metrics_service.record_query(is_cached=False, is_escalated=is_escalated, tokens=350)

            return chat_response

        except Exception as e:
            return ChatResponse(
                response=f"Ocurrió un inconveniente temporal al procesar tu solicitud. Por favor intenta de nuevo o comunícate vía WhatsApp: {settings.WHATSAPP_URL}",
                is_escalated=True,
                whatsapp_link=settings.WHATSAPP_URL,
                sources=sources_list,
                session_id=session_id
            )
