import os
import re
import time
import logging
import urllib.parse
from typing import Dict, Any, List, Optional
from groq import Groq, RateLimitError
from app.core.config import settings
from app.db.vector_store import VectorStore
from app.db.cache import response_cache
from app.services.metrics_service import metrics_service
from app.schemas.chat import ChatResponse, SourceDocument

logger = logging.getLogger("lumina.rag")

def _build_whatsapp_link(user_message: str) -> str:
    """Build a direct WhatsApp URL with pre-filled advisor consultation message."""
    base_url = settings.WHATSAPP_URL
    message_text = f"Hola, me gustaría atención personalizada con el asesor Cristiano Ronaldo de Academia Lumina. Mi consulta es: \"{user_message}\""
    encoded_text = urllib.parse.quote(message_text)
    return f"{base_url}?text={encoded_text}"

def _sanitize_pii(text: str) -> str:
    """Mask or redact sensitive personally identifiable information (PII) from responses."""
    if not text:
        return ""
    # Mask national identification numbers (cédula, CC, ID)
    cleaned = re.sub(
        r'\b(cédula|cedula|cc|documento|identificación|identificacion|id)\s*[:\.]?\s*[\d.\-]{6,12}\b',
        r'\1 [ID PROTECTED]',
        text,
        flags=re.IGNORECASE
    )
    # Mask Colombian mobile phone numbers
    cleaned = re.sub(r'\+?57[\s.\-]?3\d{2}[\s.\-]?\d{3}[\s.\-]?\d{4}', '[PHONE PROTECTED]', cleaned)
    cleaned = re.sub(r'\b3\d{2}[\s.\-]?\d{3}[\s.\-]?\d{4}\b', '[PHONE PROTECTED]', cleaned)
    return cleaned.strip()

def _is_unrelated_query(user_message: str) -> bool:
    """Check if query is completely off-topic (math calculations, jokes, coding, unrelated general topics)."""
    msg_lower = user_message.lower().strip()
    
    # Mathematical expression / arithmetic questions (e.g. "cuanto es 100 + 100", "2+2", "50 * 3")
    math_pattern = r'(\d+\s*[\+\-\*\/xX÷]\s*\d+)|(cu[aá]nto\s+es\s+\d+)|(calcula\s+\d+)|(what\s+is\s+\d+)'
    if re.search(math_pattern, msg_lower):
        return True
    
    # Generic non-academy topics
    off_topic_keywords = [
        "chiste", "cuentame un chiste", "tell me a joke", "quien gano el mundial", 
        "capital de", "clima hoy", "receta de", "hazme un codigo", "write python code"
    ]
    if any(k in msg_lower for k in off_topic_keywords):
        return True
        
    return False

def _check_strict_escalation(user_message: str, assistant_response: str) -> bool:
    """
    Determine if a user query requires human advisor escalation.
    Never escalates if the topic is covered in the knowledge base (programs, prices, levels, schedules, modalities)
    or if it is completely off-topic/unrelated.
    """
    msg_lower = user_message.lower()
    resp_lower = assistant_response.lower()

    # Off-topic or math queries should never escalate
    if _is_unrelated_query(user_message):
        return False

    # Topics that the bot must answer directly without escalating
    in_scope_terms = [
        "programa", "program", "precio", "price", "costo", "cost", "horario", "schedule", 
        "nivel", "level", "inscripcion", "inscripción", "enrollment", "admission", 
        "certific", "presencial", "in-person", "virtual", "online", "inglés", "english", 
        "francés", "french", "portugués", "portuguese", "valor", "cuanto", "cuánto"
    ]

    # Explicit out-of-scope topics that require human advisor
    out_of_scope_terms = [
        "intercambio", "exchange", "beca", "scholarship", "tour", "corporativo", "corporate", 
        "canadá", "canada", "exterior", "abroad", "suiza", "switzerland", "alemania", "germany", "visa"
    ]

    # If query is in-scope and not asking about out-of-scope subjects, do not escalate
    if any(term in msg_lower for term in in_scope_terms) and not any(term in msg_lower for term in out_of_scope_terms):
        return False

    # Escalate only if explicitly requesting an out-of-scope service or LLM explicitly lacked official records
    if any(term in msg_lower for term in out_of_scope_terms):
        return True

    if "no cuento con información" in resp_lower or "registros oficiales" in resp_lower or "official records" in resp_lower:
        return True

    return False

SYSTEM_PROMPT = f"""
Eres el Asistente Inteligente de Atención al Cliente de 'Academia Lumina', una reconocida academia de idiomas en Colombia.

TU OBJETIVO:
Responder de forma clara, natural, profesional y directa las dudas de estudiantes sobre programas de idiomas (inglés, francés, portugués), precios, modalidades (presencial y virtual), horarios, inscripciones y certificaciones.

REGLAS DE COMPORTAMIENTO Y TONO DE RESPUESTA:
1. RESPONDER CONSULTAS DE PROGRAMAS Y PRECIOS DIRECTAMENTE: Si el estudiante pregunta sobre programas disponibles, precios, niveles, inscripciones u horarios, DEBES responder la información completa directamente con los datos de la base de conocimientos. NO lo remitas a un asesor si la respuesta está en el contexto.
2. SIN SALUDOS REPETITIVOS: NO repitas saludos largos o formales en cada respuesta. Responde directamente a la consulta de forma natural, profesional y continua.
3. EXPLICACIÓN CLARA Y COMPLETA: Da respuestas concretas, profesionales y bien estructuradas que resuelvan la duda totalmente sin dejar ambigüedades. No pegues títulos fríos de Markdown ni números telefónicos crudos.
4. PROTECCIÓN DE DATOS SENSIBLES (PII): Nunca imprimas cédulas, números de identificación personal o números telefónicos crudos en el texto.
5. REGLA ESTRICTA ANTI-ALUCINACIÓN: Responde ÚNICAMENTE basándote en la información proporcionada en la sección 'CONTEXTO DE NEGOCIO'. No inventes datos no escritos en el contexto.
6. PREGUNTAS NO RELACIONADAS O MATEMÁTICAS (OFF-TOPIC): Si el usuario realiza preguntas ajenas a Academia Lumina (ej: operaciones matemáticas como 'cuánto es 100 + 100', acertijos, programación o cultura general), responde amablemente que solo estás programado para responder dudas sobre los cursos e inscripciones de Academia Lumina. NO escales a asesor ni ofrezcas formulario.
7. REGLA DE ESCALAMIENTO FUERA DE ALCANCE (OUT-OF-SCOPE): ÚNICAMENTE si la pregunta se refiere a un tema institucional NO cubierto en el contexto (por ejemplo: intercambios culturales al exterior, sedes en Canadá, becas deportivas o convenios corporativos a medida), indica profesionalmente que no posees esa información e invita al usuario a diligenciar sus datos para conectarse con un asesor:
"No cuento con información sobre la presencia o habilitación del tema solicitado en nuestros registros oficiales. Para conectarte directamente con nuestro asesor Cristiano Ronaldo por WhatsApp, por favor completa tus datos en el formulario desplegado a continuación."
"""

OFF_TOPIC_RESPONSE = "Solo estoy programado para resolver dudas sobre los programas de idiomas, precios, horarios, modalidades e inscripciones de Academia Lumina. ¿En qué te puedo colaborar respecto a nuestros cursos?"

class RAGService:
    """Core RAG service integrating ChromaDB vector storage, memory TTL cache, and Groq LLM inference."""

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """Initialize Groq client and ChromaDB vector store."""
        self.vector_store = vector_store or VectorStore(collection_name="academia_lumina_kb")
        self.groq_api_key = settings.GROQ_API_KEY
        self.client = None
        if self.groq_api_key and not self.groq_api_key.startswith("gsk_your"):
            self.client = Groq(api_key=self.groq_api_key)

    def generate_response(self, user_message: str, session_id: str = "default") -> ChatResponse:
        """Process user query, check cache, retrieve vector context, and generate response via Groq."""
        # 0. Check for off-topic / unrelated queries (e.g. math 100+100, trivia)
        if _is_unrelated_query(user_message):
            return ChatResponse(
                response=OFF_TOPIC_RESPONSE,
                is_escalated=False,
                whatsapp_link=None,
                sources=[],
                session_id=session_id
            )

        # 1. Check TTL cache
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

        # 2. Semantic search in ChromaDB
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

RESPUESTA DEL ASISTENTE:
"""

        # 3. Fallback mode if Groq API key is not configured
        if not self.client:
            is_escalated = _check_strict_escalation(user_message, "")
            if is_escalated:
                resp_text = (
                    "No cuento con información sobre la presencia o habilitación del tema solicitado en nuestros registros oficiales. "
                    "Para conectarte directamente con nuestro asesor Cristiano Ronaldo por WhatsApp, por favor completa tus datos en el formulario a continuación."
                )
                wa_link = _build_whatsapp_link(user_message)
            else:
                best_match = search_results[0]['content'] if search_results else 'Consulta sobre programas.'
                for res in search_results:
                    if any(word in res['content'].lower() for word in user_message.lower().split()):
                        best_match = res['content']
                        break

                clean_chunk = re.sub(r'^#{1,3}\s+.*\n?', '', best_match, flags=re.MULTILINE).strip()
                resp_text = _sanitize_pii(clean_chunk)
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

        # 4. Invoke Groq LLM with automatic retry
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

                raw_response = chat_completion.choices[0].message.content.strip()
                assistant_response = _sanitize_pii(raw_response)
                
                is_escalated = _check_strict_escalation(user_message, assistant_response)
                whatsapp_link = _build_whatsapp_link(user_message) if is_escalated else None

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
                logger.error("Groq API error on attempt %d: %s", attempt + 1, str(e), exc_info=True)
                break

        # Fallback in case of network or rate limit exhaustion
        is_escalated = _check_strict_escalation(user_message, "")
        resp_text = (
            "No cuento con información sobre la presencia o habilitación del tema solicitado en nuestros registros oficiales. "
            "Para conectarte directamente con nuestro asesor Cristiano Ronaldo por WhatsApp, por favor completa tus datos en el formulario a continuación."
        ) if is_escalated else (
            "Ocurrió un inconveniente temporal de conexión con el servicio de IA. "
            "Por favor intenta de nuevo o comunícate directamente con nuestro equipo de soporte."
        )

        return ChatResponse(
            response=_sanitize_pii(resp_text),
            is_escalated=is_escalated,
            whatsapp_link=_build_whatsapp_link(user_message) if is_escalated else None,
            sources=sources_list,
            session_id=session_id
        )
