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

def _build_whatsapp_link(user_message: str, language: str = "es") -> str:
    """Build a direct WhatsApp URL with pre-filled advisor consultation message."""
    base_url = settings.WHATSAPP_URL
    if language == "en":
        message_text = f"Hello, I would like personalized guidance from advisor Cristiano Ronaldo at Academia Lumina. My inquiry is: \"{user_message}\""
    else:
        message_text = f"Hola, me gustaría atención personalizada con el asesor Cristiano Ronaldo de Academia Lumina. Mi consulta es: \"{user_message}\""
    encoded_text = urllib.parse.quote(message_text)
    return f"{base_url}?text={encoded_text}"

def _sanitize_pii(text: str) -> str:
    """Mask or redact sensitive personally identifiable information (PII) from responses."""
    if not text:
        return ""
    cleaned = re.sub(
        r'\b(cédula|cedula|cc|documento|identificación|identificacion|id)\s*[:\.]?\s*[\d.\-]{6,12}\b',
        r'\1 [ID PROTECTED]',
        text,
        flags=re.IGNORECASE
    )
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
        "capital de", "clima hoy", "receta de", "hazme un codigo", "write python code",
        "who is the president", "tell me a story"
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

def _get_system_prompt(language: str = "en") -> str:
    """Return tailored system prompt enforcing strict response language."""
    if language == "en":
        return """
You are the AI Customer Support Specialist for 'Academia Lumina', an accredited language academy in Colombia.

CRITICAL INSTRUCTION - LANGUAGE CONSTRAINT:
You MUST respond EXCLUSIVELY in ENGLISH. Even though the business context is written in Spanish, translate and synthesize all information seamlessly into clear, professional, natural English.

YOUR GOAL:
Answer questions about language programs (English, French, Portuguese), pricing in COP, study modalities (In-person campus and Virtual Live), schedules, admissions, and CEFR certification.

RULES:
1. ANSWER IN ENGLISH ONLY.
2. ANSWER DIRECTLY FROM CONTEXT: For program details, prices, schedules, and modalities, answer immediately with complete facts. DO NOT defer to an advisor if the info exists in the context.
3. NO REPETITIVE GREETINGS: Do not repeat long formal greetings on every turn. Be concise, warm, and helpful.
4. NO PII LEAKS: Never print raw phone numbers or national IDs.
5. STRICT ANTI-HALLUCINATION: Use ONLY facts from the provided business context.
6. OFF-TOPIC / UNRELATED: If the user asks non-academy questions (math, trivia, jokes, coding), politely state that you are only programmed to assist with Academia Lumina language programs.
7. OUT-OF-SCOPE ESCALATION: ONLY if the student asks for unlisted institutional services (such as study-abroad exchange trips to Canada, sports scholarships, or customized corporate deals), respond with this exact template in English:
"I do not have information regarding the presence or availability of this topic in our official records. To connect directly with our advisor Cristiano Ronaldo on WhatsApp, please complete your details in the form displayed below."
"""
    else:
        return """
Eres el Asistente Inteligente de Atención al Cliente de 'Academia Lumina', una reconocida academia de idiomas en Colombia.

INSTRUCCIÓN CRÍTICA - IDIOMA DE RESPUESTA:
Debes responder EXCLUSIVAMENTE en ESPAÑOL de forma clara, natural, profesional y continua.

TU OBJETIVO:
Responder dudas de estudiantes sobre programas de idiomas (inglés, francés, portugués), precios en COP, modalidades (presencial y virtual en vivo), horarios, inscripciones y certificaciones MCER.

REGLAS:
1. RESPONDE SIEMPRE EN ESPAÑOL.
2. RESPONDER CONSULTAS DE PROGRAMAS Y PRECIOS DIRECTAMENTE: Si el estudiante pregunta sobre programas, precios, niveles, inscripciones u horarios, responde la información completa directamente con los datos de la base de conocimientos. NO lo remitas a un asesor si la respuesta está en el contexto.
3. SIN SALUDOS REPETITIVOS: Responde directamente a la consulta de forma continua y ejecutiva.
4. PROTECCIÓN DE DATOS SENSIBLES (PII): Nunca imprimas cédulas ni números telefónicos crudos.
5. REGLA ESTRICTA ANTI-ALUCINACIÓN: Responde ÚNICAMENTE basándote en la información proporcionada en la sección 'CONTEXTO DE NEGOCIO'.
6. PREGUNTAS NO RELACIONADAS O MATEMÁTICAS (OFF-TOPIC): Si el usuario realiza preguntas ajenas a Academia Lumina, responde amablemente que solo estás programado para resolver dudas sobre los cursos e inscripciones de Academia Lumina.
7. REGLA DE ESCALAMIENTO FUERA DE ALCANCE (OUT-OF-SCOPE): ÚNICAMENTE si la pregunta se refiere a un tema NO cubierto en el contexto (por ejemplo: intercambios culturales a Canadá, becas o convenios corporativos a medida), usa exactamente esta estructura:
"No cuento con información sobre la presencia o habilitación del tema solicitado en nuestros registros oficiales. Para conectarte directamente con nuestro asesor Cristiano Ronaldo por WhatsApp, por favor completa tus datos en el formulario desplegado a continuación."
"""

class RAGService:
    """Core RAG service integrating ChromaDB vector storage, memory TTL cache, and Groq LLM inference."""

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """Initialize Groq client and ChromaDB vector store."""
        self.vector_store = vector_store or VectorStore(collection_name="academia_lumina_kb")
        self.groq_api_key = settings.GROQ_API_KEY
        self.client = None
        if self.groq_api_key and not self.groq_api_key.startswith("gsk_your"):
            self.client = Groq(api_key=self.groq_api_key)

    def generate_response(
        self,
        user_message: str,
        session_id: str = "default",
        language: str = "en"
    ) -> ChatResponse:
        """Process user query, check cache, retrieve vector context, and generate response via Groq in the requested language."""
        lang_code = "en" if language.lower().startswith("en") else "es"
        
        # 0. Check for off-topic / unrelated queries (e.g. math 100+100, trivia)
        if _is_unrelated_query(user_message):
            off_topic_msg = (
                "I am only programmed to assist with questions regarding Academia Lumina's language programs, pricing, schedules, study modalities, and enrollment. How can I help you with our courses today?"
                if lang_code == "en" else
                "Solo estoy programado para resolver dudas sobre los programas de idiomas, precios, horarios, modalidades e inscripciones de Academia Lumina. ¿En qué te puedo colaborar respecto a nuestros cursos?"
            )
            return ChatResponse(
                response=off_topic_msg,
                is_escalated=False,
                whatsapp_link=None,
                sources=[],
                session_id=session_id
            )

        # 1. Check TTL cache
        cache_key = f"{lang_code}:{user_message}"
        cached_resp = response_cache.get(cache_key)
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

        context_str = "\n\n---\n\n".join([r["content"] for r in search_results]) if search_results else "No context available."

        system_prompt = _get_system_prompt(lang_code)
        user_prompt = f"""
ACADEMIC BUSINESS CONTEXT (RETRIEVED FROM OFFICIAL RECORDS):
{context_str}

USER QUERY:
{user_message}

ASSISTANT RESPONSE (IN {lang_code.upper()}):
"""

        # 3. Fallback mode if Groq API key is not configured
        if not self.client:
            is_escalated = _check_strict_escalation(user_message, "")
            if is_escalated:
                resp_text = (
                    "I do not have information regarding the presence or availability of this topic in our official records. To connect directly with our advisor Cristiano Ronaldo on WhatsApp, please complete your details in the form below."
                    if lang_code == "en" else
                    "No cuento con información sobre la presencia o habilitación del tema solicitado en nuestros registros oficiales. Para conectarte directamente con nuestro asesor Cristiano Ronaldo por WhatsApp, por favor completa tus datos en el formulario desplegado a continuación."
                )
                wa_link = _build_whatsapp_link(user_message, lang_code)
            else:
                best_match = search_results[0]['content'] if search_results else 'Language programs inquiry.'
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
            
            response_cache.set(cache_key, chat_response)
            metrics_service.record_query(is_cached=False, is_escalated=is_escalated, tokens=150)
            return chat_response

        # 4. Invoke Groq LLM with automatic retry
        for attempt in range(2):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model="openai/gpt-oss-120b",
                    temperature=0.3,
                    max_tokens=500
                )

                raw_response = chat_completion.choices[0].message.content.strip()
                assistant_response = _sanitize_pii(raw_response)
                
                is_escalated = _check_strict_escalation(user_message, assistant_response)
                whatsapp_link = _build_whatsapp_link(user_message, lang_code) if is_escalated else None

                chat_response = ChatResponse(
                    response=assistant_response,
                    is_escalated=is_escalated,
                    whatsapp_link=whatsapp_link,
                    sources=sources_list,
                    session_id=session_id
                )

                response_cache.set(cache_key, chat_response)
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
        if is_escalated:
            resp_text = (
                "I do not have information regarding the presence or availability of this topic in our official records. To connect directly with our advisor Cristiano Ronaldo on WhatsApp, please complete your details in the form below."
                if lang_code == "en" else
                "No cuento con información sobre la presencia o habilitación del tema solicitado en nuestros registros oficiales. Para conectarte directamente con nuestro asesor Cristiano Ronaldo por WhatsApp, por favor completa tus datos en el formulario desplegado a continuación."
            )
        else:
            resp_text = (
                "A temporary connection issue occurred with the AI service. Please try again in a few moments."
                if lang_code == "en" else
                "Ocurrió un inconveniente temporal de conexión con el servicio de IA. Por favor intenta de nuevo en unos momentos."
            )

        return ChatResponse(
            response=_sanitize_pii(resp_text),
            is_escalated=is_escalated,
            whatsapp_link=_build_whatsapp_link(user_message, lang_code) if is_escalated else None,
            sources=sources_list,
            session_id=session_id
        )
