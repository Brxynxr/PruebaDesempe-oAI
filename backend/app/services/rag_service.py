import os
import json
import re
import time
from typing import Dict, Any, List, Optional
from groq import Groq, RateLimitError
from app.core.config import settings
from app.db.vector_store import VectorStore
from app.db.cache import response_cache
from app.services.metrics_service import metrics_service
from app.services.email_service import EmailService
from app.schemas.chat import ChatResponse, SourceDocument

SYSTEM_PROMPT = f"""
Eres el Asistente Inteligente de Atención al Cliente de 'Academia Lumina', una reconocida academia de idiomas en Colombia.

TU OBJETIVO:
Responder de forma clara, natural, profesional y directa las dudas de estudiantes sobre programas de idiomas (inglés, francés, portugués), precios, modalidades (presencial y virtual), horarios, inscripciones y certificaciones.

REGLAS DE COMPORTAMIENTO Y TONO DE RESPUESTA:
1. SIN SALUDOS REPETITIVOS: NO repitas saludos largos o formales (como "¡Hola! Gracias por comunicarte con Academia Lumina...") en cada respuesta. Responde directamente a la consulta de forma natural, profesional y continua.
2. EXPLICACIÓN CLARA Y COMPLETA: Da respuestas concretas, profesionales y bien estructuradas que resuelvan la duda totalmente sin dejar ambigüedades. No pegues títulos fríos de Markdown (como ## Título) ni números telefónicos crudos.
3. NO INCLUIR NÚMEROS DE TELÉFONO NI URLS CRUDAS EN EL TEXTO: Nunca imprimas números de teléfono (como +57...) ni enlaces en el texto de tu respuesta. La interfaz gráfica desplegará el botón oficial de WhatsApp automáticamente.
4. REGLA ESTRICTA ANTI-ALUCINACIÓN: Responde ÚNICAMENTE basándote en la información proporcionada en la sección 'CONTEXTO DE NEGOCIO'. No inventes datos no escritos en el contexto.
5. REGLA DE ESCALAMIENTO FUERA DE ALCANCE (OUT-OF-SCOPE): Si la pregunta se refiere a un tema NO cubierto en el contexto (por ejemplo: intercambios culturales al exterior, sedes o programas en el extranjero como Canadá, becas deportivas, convenios corporativos a medida o tours físicos), indica profesionalmente que no posees esa información en los registros oficiales e invita al usuario a chatear con un asesor por WhatsApp mediante el botón disponible. Usa exactamente esta estructura profesional:
"No cuento con información sobre la presencia o habilitación del tema solicitado en nuestros registros oficiales. Si deseas atención personalizada, comunícate con uno de nuestros asesores por WhatsApp mediante el siguiente botón."

EJEMPLOS FEW-SHOT DE REFERENCIA:

Ejemplo 1 (Pregunta de inscripciones):
Usuario: "¿Cuándo habilitan las inscripciones?"
Asistente: "Las inscripciones en Academia Lumina se habilitan dos veces al año: para el primer semestre abren del 1 de noviembre al 20 de enero (clases inician en febrero), y para el segundo semestre del 1 de mayo al 20 de julio (clases inician en agosto), tanto para la modalidad presencial como virtual. El proceso se realiza 100% en línea."

Ejemplo 2 (Pregunta de precio directo):
Usuario: "¿Cuánto cuesta el nivel A1 de inglés?"
Asistente: "El costo del nivel A1 de inglés por semestre es de $450.000 COP en modalidad presencial y $380.000 COP en modalidad virtual. Este valor incluye el acceso a la plataforma digital y los materiales en PDF."

Ejemplo 3 (Pregunta fuera de alcance / Escalamiento):
Usuario: "¿Tienen sedes o intercambios culturales a Canadá?"
Asistente: "No cuento con información sobre la presencia o habilitación de programas en Canadá en nuestros registros oficiales. Si deseas atención personalizada, comunícate con uno de nuestros asesores por WhatsApp mediante el siguiente botón."
"""

class RAGService:
    """
    Servicio principal de RAG que integra el VectorStore de ChromaDB,
    el sistema de caché TTL en memoria y la API del modelo de Groq.
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
        search_results = self.vector_store.search(query=user_message, top_k=6)
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

RESPUESTA DEL ASISTENTE (recuerda responder directo, sin saludos repetitivos, sin números telefónicos en el texto y de forma profesional):
"""

        # 3. Si la API Key de Groq no está activa (modo desarrollo/simulado)
        if not self.client:
            is_escalated = any(term in user_message.lower() for term in ["intercambio", "beca", "tour", "corporativo", "canadá", "exterior"])
            if is_escalated:
                resp_text = (
                    "No cuento con información sobre la presencia o habilitación del tema solicitado en nuestros registros oficiales. "
                    "Si deseas atención personalizada, comunícate con uno de nuestros asesores por WhatsApp mediante el siguiente botón."
                )
                wa_link = settings.WHATSAPP_URL
                EmailService.send_escalation_email_async(user_message, resp_text, session_id)
            else:
                best_match = search_results[0]['content'] if search_results else 'Consulta sobre programas.'
                for res in search_results:
                    if any(word in res['content'].lower() for word in user_message.lower().split()):
                        best_match = res['content']
                        break

                clean_chunk = re.sub(r'^#{1,3}\s+.*\n?', '', best_match, flags=re.MULTILINE).strip()
                resp_text = clean_chunk
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

        # 4. Invocación a Groq con reintento automático si hay RateLimitError temporal
        for attempt in range(2):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    model="openai/gpt-oss-120b",
                    temperature=0.3,
                    max_tokens=500
                )

                assistant_response = chat_completion.choices[0].message.content.strip()
                
                # Eliminar números telefónicos o URLs crudas si el LLM las imprimió por error en el texto
                assistant_response = re.sub(r'\+?57\s?\d{3}\s?\d{3}\s?\d{4}', '', assistant_response).strip()
                
                is_escalated = (
                    "whatsapp" in assistant_response.lower() or 
                    "asesor" in assistant_response.lower() or
                    any(term in user_message.lower() for term in ["intercambio", "beca", "tour", "corporativo", "canadá", "exterior"])
                )
                whatsapp_link = settings.WHATSAPP_URL if is_escalated else None

                if is_escalated:
                    EmailService.send_escalation_email_async(user_message, assistant_response, session_id)

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

            except RateLimitError:
                if attempt == 0:
                    time.sleep(0.3)
                    continue
                else:
                    break
            except Exception as e:
                break

        # Fallback en caso de agotar reintentos o error de red
        is_escalated = any(term in user_message.lower() for term in ["intercambio", "beca", "tour", "corporativo", "canadá", "exterior"])
        resp_text = (
            "No cuento con información sobre la presencia o habilitación del tema solicitado en nuestros registros oficiales. "
            "Si deseas atención personalizada, comunícate con uno de nuestros asesores por WhatsApp mediante el siguiente botón."
        ) if is_escalated else (
            "Ocurrió un inconveniente temporal de conexión con el servicio de IA. "
            "Por favor intenta de nuevo o comunícate directamente con nuestro equipo de soporte."
        )

        if is_escalated:
            EmailService.send_escalation_email_async(user_message, resp_text, session_id)

        return ChatResponse(
            response=resp_text,
            is_escalated=is_escalated,
            whatsapp_link=settings.WHATSAPP_URL if is_escalated else None,
            sources=sources_list,
            session_id=session_id
        )
