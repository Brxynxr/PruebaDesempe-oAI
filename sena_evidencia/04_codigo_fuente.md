# 04. Estructura del Código Fuente e Implementación: Academia Lumina AI

Este documento expone la topología física de archivos, la descripción funcional de cada directorio, el flujo de procesamiento de extremo a extremo, fragmentos de código fuente reales extraídos directamente de la base de código y el inventario formal de dependencias.

---

## 1. Árbol de Directorios del Proyecto

```text
PruebaDesempe-oAI/
├── backend/                                # Núcleo del servidor API REST y WebSockets (FastAPI)
│   ├── app/
│   │   ├── api/                            # Capa de controladores y enrutamiento HTTP
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── admin.py            # Autenticación JWT, subida de archivos y gestión de casos
│   │   │       │   ├── chat.py             # Endpoint RAG (/chat) y captura de prospectos (/lead)
│   │   │       │   ├── health.py           # Sondas de salud (/health y /)
│   │   │       │   ├── metrics.py          # Exposición de métricas de SLA, CSAT y tokens (/metrics)
│   │   │       │   └── websocket.py        # Canales en tiempo real (/ws/chat y /ws/agent)
│   │   │       └── api.py                  # Agregador de rutas de la versión 1
│   │   ├── core/                           # Configuraciones globales y políticas de seguridad
│   │   │   ├── auth.py                     # Encriptación de contraseñas Bcrypt y emisión/verificación JWT
│   │   │   ├── config.py                   # Esquema de variables de entorno con Pydantic Settings
│   │   │   ├── guardrails.py               # Defensa contra Prompt Injections y normalización NFKD
│   │   │   └── security.py                 # Limitador de tasa (SlowAPI) y validación de API Key
│   │   ├── data/                           # Base de conocimiento oficial (PDFs y Word DOCX curriculares)
│   │   │   ├── certificaciones_y_diplomas_oficiales.docx
│   │   │   ├── convenios_corporativos_y_becas.pdf
│   │   │   ├── guia_academica_y_programas_2026.pdf
│   │   │   └── manual_admisiones_y_pagos.docx
│   │   ├── db/                             # Persistencia relacional, vector store y caché
│   │   │   ├── cache.py                    # Caché en memoria TTL (1h) para consultas frecuentes
│   │   │   ├── models.py                   # Modelos ORM SQLAlchemy (Conversation, Message, AdminUser)
│   │   │   ├── repository.py               # Operaciones CRUD y operaciones atómicas de asignación
│   │   │   ├── session.py                  # Conexión a SQLite local o PostgreSQL en la nube
│   │   │   └── vector_store.py             # Cliente ChromaDB para búsqueda por similitud vectorial
│   │   ├── schemas/                        # Contratos de datos (Pydantic v2)
│   │   │   ├── admin.py                    # DTOs de login, métricas y administración
│   │   │   └── chat.py                     # DTOs de solicitudes y respuestas de chat
│   │   ├── services/                       # Lógica de dominio y servicios desacoplados
│   │   │   ├── cleanup_service.py          # Demonio en segundo plano de auto-limpieza (30 min)
│   │   │   ├── connection_manager.py       # Gestor en memoria de conexiones WebSocket activas
│   │   │   ├── email_service.py            # Despacho de notificaciones por correo SMTP
│   │   │   ├── ingestion_service.py        # Extracción y chunking de PDF, DOCX, MD y TXT
│   │   │   ├── metrics_service.py          # Motor de cálculo analítico de SLAs, costos y CSAT
│   │   │   ├── rag_service.py              # Inferencia conversacional con Groq LPU y ChromaDB
│   │   │   └── telegram_service.py         # Bot de Telegram y teclados de acción rápida
│   │   ├── __init__.py
│   │   ├── lumina.db                       # Base de datos SQLite (desarrollo local)
│   │   └── main.py                         # Punto de entrada FastAPI con ciclo de vida (Lifespan)
│   ├── tests/                              # Suite de pruebas automatizadas (47 tests / 14 suites)
│   │   ├── conftest.py                     # Fixtures compartidas de FastAPI TestClient y mocks
│   │   ├── test_admin_auth.py              # Pruebas de hash, login y aislamiento de roles
│   │   ├── test_cache.py                   # Pruebas de aciertos, fallos y expiración TTL
│   │   ├── test_cors.py                    # Pruebas de orígenes permitidos y denegados
│   │   ├── test_documents_upload.py        # Pruebas de subida y reindexación vectorial de archivos
│   │   ├── test_edge_cases.py              # Pruebas de spoofing IP, fallback bilingüe y contexto
│   │   ├── test_email_service.py           # Pruebas de despacho SMTP
│   │   ├── test_escalation_lifecycle.py    # Pruebas del ciclo de vida y detección de brechas SLA
│   │   ├── test_health.py                  # Pruebas de endpoints de salud
│   │   ├── test_metrics.py                 # Pruebas de agregación de métricas
│   │   ├── test_rag_search.py              # Pruebas de chunking e indexación en ChromaDB
│   │   ├── test_rag_service.py             # Pruebas de respuestas in-scope y out-of-scope
│   │   ├── test_rate_limit.py              # Pruebas de bloqueo por exceso de solicitudes
│   │   ├── test_real_tokens_metrics.py     # Pruebas de estimación de costos y tokens
│   │   ├── test_security.py                # Pruebas de autenticación y guardrails anti-inyección
│   │   └── test_telegram_isolation.py      # Pruebas de aislamiento de comandos en Telegram
│   ├── Dockerfile                          # Contenedor Python 3.12 optimizado
│   └── requirements.txt                    # Dependencias estrictas del backend
├── frontend/                               # Interfaz de usuario (React 18 + Vite 5 SPA)
│   ├── public/                             # Activos estáticos públicos (Favicon SVG)
│   ├── src/
│   │   ├── assets/                         # Fotografías institucionales optimizadas
│   │   ├── components/
│   │   │   ├── AdminDashboard.jsx          # Panel del Asesor: Inbox en vivo, Métricas y Documentos
│   │   │   ├── AdminLogin.jsx              # Formulario de inicio de sesión con JWT
│   │   │   ├── FloatingChat.jsx            # Widget flotante con soporte HTTP fallback y WebSockets
│   │   │   └── LandingPage.jsx             # Página de bienvenida con oferta académica
│   │   ├── lib/                            # Utilidades de estilos (cn para Tailwind)
│   │   ├── services/
│   │   │   └── api.js                      # Cliente Axios/Fetch configurado con tokens y URLs
│   │   ├── App.jsx                         # Enrutador principal de la aplicación (/ y /admin)
│   │   ├── main.jsx                        # Montaje en el DOM de React
│   │   └── styles.css                      # Estilos personalizados y utilidades Tailwind v4
│   ├── Dockerfile                          # Contenedor Node.js multi-stage con Nginx
│   ├── nginx.conf                          # Configuración de Nginx para enrutamiento SPA
│   ├── package.json                        # Dependencias de Node (React, Lucide, Tailwind)
│   └── vite.config.js                      # Configuración del bundler Vite
├── n8n/                                    # Flujos de automatización declarativos
│   ├── workflow.json                       # Flujo principal de escalamiento a Telegram con botones
│   ├── workflow_leads.json                 # Flujo para captura y consolidación de prospectos
│   ├── workflow_sla.json                   # Cron de monitoreo de tickets vencidos (>15 min)
│   ├── workflow_reportes.json              # Cron matutino (8:00 AM) para reporte ejecutivo
│   └── README_N8N.md                       # Manual de importación y configuración en n8n
├── documents/                              # Documentación técnica compilada
│   ├── Documentacion_Academia_Lumina_AI.docx # Documento formal en formato Word institucional
│   └── docs.html                           # Vista web autocontenida de la documentación
├── sena_evidencia/                         # Paquete de evidencias para evaluación SENA
│   ├── 01_diseno_software.md
│   ├── 02_uml.md
│   ├── 03_modelo_datos.md
│   ├── 04_codigo_fuente.md
│   ├── 05_manual_de_uso.md
│   ├── 06_capturas_pendientes.md
│   └── screenshots/                        # Capturas reales de la aplicación en ejecución
├── docker-compose.yml                      # Orquestación de contenedores (Backend, Frontend, n8n)
├── docs.md                                 # Especificación técnica base
├── GUIA_DESPLIEGUE_Y_N8N.md                # Guía paso a paso de despliegue y workflows
├── README.md                               # Guía rápida de presentación del proyecto
├── RENDER_DEPLOYMENT.md                    # Manual de despliegue en Render Cloud
└── render.yaml                             # Especificación declarativa de infraestructura Render
```

---

## 2. Flujo del Sistema de Punta a Punta

1. **Ingreso y Consulta**: El usuario accede a la landing page y abre el widget `FloatingChat.jsx`. Escribe una consulta.
2. **Defensa Perimetral**: La petición `POST /api/v1/chat` pasa por `SlowAPI` (valida que la IP no exceda 10 req/min) y por `guardrails.py` (normaliza Unicode y descarta ataques de inyección de prompt).
3. **Caché y Persistencia**: El controlador guarda el mensaje en la tabla `messages` vía `repository.py` y consulta `ResponseCache`. Si la pregunta ya fue respondida recientemente, se retorna el texto de inmediato sin gastar cuota de API.
4. **Búsqueda Vectorial RAG**: En caso de fallo de caché, `rag_service.py` genera la consulta semántica contra `ChromaDB` (`vector_store.py`), rescatando los fragmentos curriculares más relevantes con su respectiva fuente.
5. **Generación con Groq LPU**: Se ensambla el prompt de sistema con las directrices institucionales, el contexto de los documentos y el historial previo. La API de Groq responde en ~400-700ms.
6. **Escalamiento Asistido (Live Handoff)**: Si el usuario requiere un humano ("quiero un asesor"), el estado cambia a `pendiente`. `FloatingChat` abre un WebSocket `/ws/chat/{session_id}`. Simultáneamente, el backend emite un webhook a n8n que dispara un mensaje a Telegram con botones interactivos y notifica a los asesores conectados en el panel web.
7. **Atención en Vivo**: Un asesor hace clic en `[Tomar Caso]` en la web o Telegram. La conversación pasa a `en_atencion`. Todo lo que el asesor escribe en `/ws/agent` viaja instantáneamente al chat del estudiante mediante `ConnectionManager`.
8. **Cierre de Ciclo**: El asesor hace clic en `[Caso Resuelto]`. El estado pasa a `resuelto`. Al cumplirse 30 minutos, `CleanupService` purga la conversación liberando espacio.

---

## 3. Fragmentos de Código Fuente Reales

### 3.1 Endpoint de Chat con Rate Limiting y Guardrails
*Ubicación: `backend/app/api/v1/endpoints/chat.py`*

```python
# Fragmento real del endpoint de procesamiento conversacional
@router.post(
    "/chat", 
    response_model=ChatResponse, 
    summary="Process query with RAG, Groq and 4 security layers"
)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
async def handle_chat_message(
    request: Request,
    payload: ChatRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
) -> ChatResponse:
    # Capa 3: Validación estricta contra Prompt Injection con normalización Unicode NFKD
    validate_prompt_injection(payload.message)

    # Persistencia de la sesión y mensaje del usuario
    ConversationRepository.get_or_create_conversation(db, payload.session_id, idioma=payload.language)
    ConversationRepository.add_message(db, payload.session_id, remitente="user", contenido=payload.message)

    # Inferencia conversacional mediante servicio RAG
    result = await rag_service.answer_query(
        question=payload.message,
        session_id=payload.session_id,
        language=payload.language,
        history=payload.history
    )

    # Persistencia de la respuesta generada por la IA
    ConversationRepository.add_message(db, payload.session_id, remitente="bot", contenido=result["response"])

    return ChatResponse(
        response=result["response"],
        sources=result["sources"],
        session_id=payload.session_id,
        requires_escalation=result["requires_escalation"],
        lead_detected=result["lead_detected"],
        tokens_used=result["tokens_used"],
        cost_saved_usd=result["cost_saved_usd"]
    )
```

### 3.2 Lógica de Inferencia RAG con Groq y Fallback Multilingüe
*Ubicación: `backend/app/services/rag_service.py`*

```python
# Fragmento real del método principal de consulta RAG
async def answer_query(self, question: str, session_id: str, language: str = "es", history: list = None) -> dict:
    detected_lang = self._detect_language(question)
    target_lang = detected_lang if detected_lang in ["es", "en"] else language

    # Verificación en memoria caché
    cached_data = self.cache.get(target_lang, question)
    if cached_data:
        return {
            "response": cached_data["response"],
            "sources": cached_data["sources"],
            "requires_escalation": False,
            "lead_detected": False,
            "tokens_used": 0,
            "cost_saved_usd": 0.0025
        }

    # Búsqueda semántica en ChromaDB
    relevant_chunks = self.vector_store.query_similar(question, n_results=3)
    context_text = "\n\n".join(relevant_chunks) if relevant_chunks else "No relevant context found."

    # Construcción de prompt institucional
    prompt = self._build_prompt(context=context_text, question=question, language=target_lang, history=history)

    try:
        response_text, token_stats = await self._call_groq_llm(prompt)
        self.cache.set(target_lang, question, {"response": response_text, "sources": ["Oficial Lumina KB"]})
        return {
            "response": response_text,
            "sources": ["Documentos Oficiales Academia Lumina 2026"],
            "requires_escalation": self._check_escalation_triggers(question),
            "lead_detected": self._check_lead_signals(question),
            "tokens_used": token_stats.get("total_tokens", 0),
            "cost_saved_usd": 0.0
        }
    except Exception as e:
        logger.error("[RAGService] Error en inferencia Groq: %s", str(e))
        # Fallback elegante bilingüe sin interrumpir al usuario
        return {
            "response": self._fallback_response(target_lang),
            "sources": [],
            "requires_escalation": True,
            "lead_detected": False,
            "tokens_used": 0,
            "cost_saved_usd": 0.0
        }
```

### 3.3 Gestor de WebSockets Bidireccionales para Live Handoff
*Ubicación: `backend/app/services/connection_manager.py`*

```python
# Fragmento real de ConnectionManager para comunicación en tiempo real
class ConnectionManager:
    def __init__(self):
        self.active_user_connections: Dict[str, List[WebSocket]] = {}
        self.active_agent_connections: Set[WebSocket] = set()

    async def connect_user(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_user_connections:
            self.active_user_connections[session_id] = []
        self.active_user_connections[session_id].append(websocket)
        logger.info("[WebSocket] User connected on session: %s", session_id)

    async def connect_agent(self, websocket: WebSocket):
        await websocket.accept()
        self.active_agent_connections.add(websocket)
        logger.info("[WebSocket] Agent connected to live channel")

    async def send_to_user(self, session_id: str, message: dict):
        """Envía un paquete JSON a todos los sockets abiertos por una sesión de estudiante."""
        if session_id in self.active_user_connections:
            for connection in list(self.active_user_connections[session_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect_user(connection, session_id)

    async def broadcast_to_agents(self, message: dict):
        """Difunde un evento a las consolas de todos los asesores conectados."""
        for connection in list(self.active_agent_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect_agent(connection)
```

### 3.4 Asignación Atómica de Conversaciones (Prevención de Race Conditions)
*Ubicación: `backend/app/db/repository.py`*

```python
# Fragmento real de asignación con lock a nivel de sentencia UPDATE
@staticmethod
def claim_conversation(db: Session, conversation_id: int, agent_username: str) -> Optional[Conversation]:
    """
    Reclama atómicamente una conversación para un asesor evitando colisiones.
    Solo aplica la transición si el registro se encuentra actualmente en estado 'pendiente'.
    """
    stmt = (
        update(Conversation)
        .where(Conversation.id == conversation_id, Conversation.estado == "pendiente")
        .values(
            estado="en_atencion",
            agente_asignado=agent_username,
            updated_at=datetime.now(timezone.utc)
        )
    )
    res = db.execute(stmt)
    db.commit()
    
    # Si rowcount > 0, este asesor ganó la asignación atómicamente
    if res.rowcount > 0:
        return ConversationRepository.get_conversation_by_id(db, conversation_id)
    
    # Si ya fue reclamada por el mismo agente previamente, se retorna la sesión activa
    conv = ConversationRepository.get_conversation_by_id(db, conversation_id)
    if conv and conv.estado == "en_atencion" and conv.agente_asignado == agent_username:
        return conv
    return None
```

---

## 4. Inventario de Tecnologías y Librerías

### 4.1 Backend (Python 3.12)
| Librería | Versión | Propósito en el Proyecto |
| :--- | :--- | :--- |
| `fastapi` | `0.110.0` | Framework web reactivo de alto rendimiento para API REST y WebSockets. |
| `uvicorn` | `0.28.0` | Servidor ASGI de producción para ejecutar FastAPI con soporte asíncrono. |
| `pydantic` | `2.6.0` | Validación estricta de esquemas de datos y contratos DTO. |
| `pydantic-settings`| `2.2.0` | Carga tipada de variables de entorno desde `.env`. |
| `sqlalchemy` | `2.0.28` | ORM declarativo para modelado relacional y operaciones con la base de datos. |
| `psycopg2-binary` | `2.9.9` | Adaptador PostgreSQL para despliegue de base de datos en Render. |
| `groq` | `0.4.2` | SDK oficial para inferencia ultrarrápida con unidades LPU de Groq Cloud. |
| `chromadb` | `0.4.24` | Almacén de vectores embebido para persistencia e indexación RAG. |
| `pypdf` | `4.0.0` | Extracción de texto desde manuales y guías en formato PDF. |
| `python-docx` | `1.1.0` | Extracción de texto estructurado desde documentos Word (.docx). |
| `slowapi` | `0.1.9` | Limitador de tasa (Rate Limiting) perimetral contra ataques DoS. |
| `pyjwt` | `2.8.0` | Generación y verificación criptográfica de tokens de sesión JWT. |
| `passlib[bcrypt]` | `1.7.4` | Algoritmo de hashing salteado unidireccional para contraseñas de asesores. |
| `pytest` | `8.0.0` | Framework de pruebas automatizadas para backend. |
| `httpx` | `0.27.0` | Cliente HTTP asíncrono utilizado en las pruebas de integración con TestClient. |

### 4.2 Frontend (Node 20+ / React 18)
| Paquete | Versión | Propósito en el Proyecto |
| :--- | :--- | :--- |
| `react` | `18.2.0` | Biblioteca base para la construcción de interfaces interactivas por componentes. |
| `react-dom` | `18.2.0` | Renderizador para la plataforma web. |
| `vite` | `5.4.21` | Bundler y servidor de desarrollo moderno con Hot Module Replacement (HMR). |
| `@tailwindcss/vite`| `4.0.0` | Compilador nativo de utilidades Tailwind CSS v4 para estilos CSS modernos. |
| `lucide-react` | `0.469.0` | Conjunto completo de iconografía SVG accesible y consistente. |
| `clsx` / `tailwind-merge` | `2.1.1` / `2.5.5` | Utilidades para interpolación condicional limpia de clases CSS. |
