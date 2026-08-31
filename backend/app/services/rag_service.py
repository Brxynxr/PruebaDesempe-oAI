import os
import json
import re
import time
import logging
import urllib.parse

logger = logging.getLogger("lumina.rag")
from typing import Dict, Any, List, Optional
from groq import Groq, RateLimitError
from app.core.config import settings
from app.db.vector_store import VectorStore
from app.db.cache import response_cache
from app.services.metrics_service import metrics_service
from app.schemas.chat import ChatResponse, SourceDocument

def _build_whatsapp_link(user_message: str) -> str:
    """
    Construye una URL directa a WhatsApp adjuntando el parámetro ?text= pre-diligenciado con la consulta del usuario.
    """
    base_url = settings.WHATSAPP_URL
    message_text = f"Hola, me gustaría atención personalizada con el asesor Cristiano Ronaldo de Academia Lumina. Mi consulta es: \"{user_message}\""
    encoded_text = urllib.parse.quote(message_text)
    return f"{base_url}?text={encoded_text}"

def _sanitize_pii(text: str) -> str:
    """
    Enmascara o remueve información sensible de las respuestas (teléfonos, cédulas de ciudadanía, IDs).
    """
    if not text:
        return ""
    # 1. Enmascarar números de cédula / documento (6 a 10 dígitos) precedidos por cc/cédula/documento
    cleaned = re.sub(r'\b(cédula|cedula|cc|documento|identificación|identificacion)\s*[:\.]?\s*[\d.\-]{6,12}\b', r'\1 [ID PROTECTED]', text, flags=re.IGNORECASE)
    # 2. Enmascarar números de teléfono móvil de 10 dígitos o con prefijo +57
    cleaned = re.sub(r'\+?57[\s.\-]?3\d{2}[\s.\-]?\d{3}[\s.\-]?\d{4}', '[PHONE PROTECTED]', cleaned)
    cleaned = re.sub(r'\b3\d{2}[\s.\-]?\d{3}[\s.\-]?\d{4}\b', '[PHONE PROTECTED]', cleaned)
    return cleaned.strip()

def _check_strict_escalation(user_message: str, assistant_response: str) -> bool:
    """
    Determina si una consulta debe ser escalada al formulario de asesor de forma estricta.
    NUNCA escala si la pregunta es sobre programas disponibles, precios, modalidades u horarios
    que están presentes en la base de conocimientos RAG.
    """
    msg_lower = user_message.lower()
    resp_lower = assistant_response.lower()

    # Términos explícitos que indican fuera de alcance oficial
    out_of_scope_terms = ["intercambio", "beca", "tour", "corporativo", "canadá", "exterior", "suiza", "alemania", "visa", "francia sedes"]
    
    # Términos de temas que la IA SÍ debe responder directamente sin escalar
    in_scope_terms = ["programa", "precio", "costo", "horario", "nivel", "inscripcion", "inscripción", "certific", "presencial", "virtual", "inglés", "francés", "portugués", "valor", "cuanto", "cuánto"]

    # Si la pregunta es sobre temas de negocio cubiertos en la KB, responder directamente sin escalar
    if any(term in msg_lower for term in in_scope_terms) and not any(term in msg_lower for term in out_of_scope_terms):
        return False

    # Escalar SOLO si el mensaje contiene términos fuera de alcance o si el LLM explícitamente no encontró registros
    if any(term in msg_lower for term in out_of_scope_terms):
        return True

    if "no cuento con información" in resp_lower or "registros oficiales" in resp_lower:
        return True

    return False

SYSTEM_PROMPT = f"""
Eres el Asistente Inteligente de Atención al Cliente de 'Academia Lumina', una reconocida academia de idiomas en Colombia.

TU OBJETIVO:
Responder de forma clara, natural, profesional y directa las dudas de estudiantes sobre programas de idiomas (inglés, francés, portugués), precios, modalidades (presencial y virtual), horarios, inscripciones y certificaciones.

REGLAS DE COMPORTAMIENTO Y TONO DE RESPUESTA:
1. RESPONDER CONSULTAS DE PROGRAMAS Y PRECIOS DIRECTAMENTE: Si el estudiante pregunta sobre programas disponibles, precios, niveles, inscripciones u horarios, DEBES responder la información completa directamente con los datos de la base de conocimientos. NO lo remitas a un asesor si la respuesta está en el contexto.
2. SIN SALUDOS REPETITIVOS: NO repitas saludos largos o formales (como "¡Hola! Gracias por comunicarte con Academia Lumina...") en cada respuesta. Responde directamente a la consulta de forma natural, profesional y continua.
3. EXPLICACIÓN CLARA Y COMPLETA: Da respuestas concretas, profesionales y bien estructuradas que resuelvan la duda totalmente sin dejar ambigüedades. No pegues títulos fríos de Markdown (como ## Título) ni números telefónicos crudos.
4. PROTECCIÓN DE DATOS SENSIBLES (PII): Nunca imprimas cédulas, números de identificación personal o números telefónicos crudos en el texto.
5. REGLA ESTRICTA ANTI-ALUCINACIÓN: Responde ÚNICAMENTE basándote en la información proporcionada en la sección 'CONTEXTO DE NEGOCIO'. No inventes datos no escritos en el contexto.
6. REGLA DE ESCALAMIENTO FUERA DE ALCANCE (OUT-OF-SCOPE): ÚNICAMENTE si la pregunta se refiere a un tema NO cubierto en el contexto (por ejemplo: intercambios culturales al exterior, sedes o programas en el extranjero como Canadá, becas deportivas, convenios corporativos a medida o tours físicos), indica profesionalmente que no posees esa información e invita al usuario a diligenciar sus datos para conectarse con un asesor. Usa exactamente esta estructura profesional:
"No cuento con información sobre la presencia o habilitación del tema solicitado en nuestros registros oficiales. Para conectarte directamente con nuestro asesor Cristiano Ronaldo por WhatsApp, por favor completa tus datos en el formulario desplegado a continuación."

EJEMPLOS FEW-SHOT DE REFERENCIA:

Ejemplo 1 (Pregunta de programas y asesoría):
Usuario: "Comunícame con un asesor para hablar sobre programas disponibles"
Asistente: "En Academia Lumina ofrecemos tres programas principales de idiomas: 1. Programa de Inglés General y Avanzado, 2. Programa de Francés Intensivo y Estándar, y 3. Programa de Portugués de Negocios. Todos los programas cuentan con modalidades Presencial (en sede Colombia) y Virtual en vivo. ¿Sobre cuál de estos tres idiomas te gustaría consultar precios y horarios?"

Ejemplo 2 (Pregunta de precio directo):
Usuario: "¿Cuánto cuesta el nivel A1 de inglés?"
Asistente: "El costo del nivel A1 de inglés por semestre es de $450.000 COP en modalidad presencial y $380.000 COP en modalidad virtual. Este valor incluye el acceso a la plataforma digital y los materiales en PDF."

Ejemplo 3 (Pregunta fuera de alcance / Escalamiento):
Usuario: "¿Tienen sedes o intercambios culturales a Canadá?"
Asistente: "No cuento con información sobre la presencia o habilitación de programas en Canadá en nuestros registros oficiales. Para conectarte directamente con nuestro asesor Cristiano Ronaldo por WhatsApp, por favor completa tus datos en el formulario desplegado a continuación."
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

RESPUESTA DEL ASISTENTE (recuerda responder directo, sin saludos repetitivos, sin números telefónicos ni cédulas y respondiendo sobre los programas si están en el contexto):
"""

        # 3. Si la API Key de Groq no está activa (modo desarrollo/simulado)
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

        # Fallback en caso de agotar reintentos o error de red
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
