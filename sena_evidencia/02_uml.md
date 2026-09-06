# 02. Especificación y Diagramas UML: Academia Lumina AI

Este documento contiene la descripción textual detallada y el modelado visual en sintaxis **Mermaid** de los casos de uso, estructura de clases y dinámicas de interacción del sistema.

---

## 1. Diagrama de Casos de Uso del Sistema

### 1.1 Actores del Sistema
1. **Estudiante / Prospecto (Web User)**: Actor primario externo que interactúa a través del widget de chat en la landing page para recibir orientación académica, consultar precios/horarios o pedir hablar con un humano.
2. **Asesor de Admisiones (Humano)**: Actor primario interno encargado de atender a los prospectos cuando se requiere atención personalizada, tanto desde la consola web (`/admin`) como desde Telegram móvil.
3. **Administrador del Sistema / Supervisor**: Actor secundario interno responsable de supervisar métricas de atención (SLA), cargar nueva documentación curricular y auditar el rendimiento del bot.
4. **Motor de Automatización (n8n Engine)**: Actor de sistema automatizado que ejecuta tareas cron periódicas (revisión de SLA, reporte matutino) y enruta webhooks hacia pasarelas de mensajería.

### 1.2 Diagrama Mermaid de Casos de Uso

```mermaid
graph LR
    actorEstudiante((Estudiante / Visitante Web))
    actorAsesor((Asesor de Admisiones))
    actorAdmin((Administrador / Supervisor))
    actorN8N((Motor n8n / Cron))

    subgraph "Sistema Academia Lumina AI"
        CU01[CU-01: Consultar Oferta Académica y Precios vía RAG]
        CU02[CU-02: Registrar Datos de Contacto / Lead]
        CU03[CU-03: Solicitar Escalamiento a Asesor Humano]
        CU04[CU-04: Chatear en Vivo con Asesor vía WebSocket]
        
        CU05[CU-05: Iniciar Sesión con JWT / Bcrypt]
        CU06[CU-06: Visualizar Bandeja de Casos Pendientes]
        CU07[CU-07: Reclamar Conversación Atómicamente - Claim]
        CU08[CU-08: Enviar Mensajes a Estudiante en Tiempo Real]
        CU09[CU-09: Marcar Conversación como Resuelta]
        CU10[CU-10: Atender / Resolver Caso desde Telegram]

        CU11[CU-11: Subir e Indexar Documentos Académicos PDF/DOCX]
        CU12[CU-12: Consultar Dashboard de Métricas y SLA]
        CU13[CU-13: Monitorear Infracciones de SLA >15 min]
        CU14[CU-14: Consolidar y Enviar Reporte Ejecutivo 8:00 AM]
    end

    actorEstudiante --> CU01
    actorEstudiante --> CU02
    actorEstudiante --> CU03
    actorEstudiante --> CU04

    actorAsesor --> CU05
    actorAsesor --> CU06
    actorAsesor --> CU07
    actorAsesor --> CU08
    actorAsesor --> CU09
    actorAsesor --> CU10

    actorAdmin --> CU05
    actorAdmin --> CU11
    actorAdmin --> CU12

    actorN8N --> CU13
    actorN8N --> CU14
```

---

## 2. Diagrama de Clases del Backend

El diagrama refleja la estructura de clases del backend en Python/FastAPI, organizadas por capas: Modelos ORM, Servicios de Negocio, Acceso a Datos y Controladores.

```mermaid
classDiagram
    class Base {
        <<DeclarativeBase>>
    }

    class Conversation {
        +int id
        +str session_id
        +str idioma
        +str estado
        +str agente_asignado
        +datetime created_at
        +datetime updated_at
        +List~Message~ messages
    }

    class Message {
        +int id
        +int conversation_id
        +str remitente
        +str contenido
        +str sender_username
        +datetime timestamp
        +Conversation conversation
    }

    class AdminUser {
        +int id
        +str username
        +str full_name
        +str role
        +bool is_active
        +str password_hash
        +datetime created_at
        +datetime updated_at
    }

    class ConversationRepository {
        -Session db
        +get_or_create_conversation(session_id, idioma) Conversation
        +get_conversation_by_session_id(session_id) Conversation
        +add_message(session_id, remitente, contenido, sender_username) Message
        +get_conversation_history(session_id, limit) List~Message~
        +get_conversations_by_status(estado) List~Conversation~
        +claim_conversation(session_id, agent_username) Tuple~bool, Conversation, str~
        +resolve_conversation(session_id, agent_username) bool
        +delete_conversation(session_id) bool
    }

    class RAGService {
        -VectorStore vector_store
        -ResponseCache cache
        +answer_query(question, session_id, language, history) Dict
        -_detect_language(query) str
        -_is_closing_intent(query) bool
        -_build_prompt(context, question, language, history) str
        -_call_groq_llm(prompt) str
        -_fallback_response(language) str
    }

    class VectorStore {
        -Client chroma_client
        -Collection collection
        +query_similar(query_text, n_results) List~str~
        +add_documents(documents, metadatas, ids) bool
        +reindex_all_data() int
    }

    class ResponseCache {
        -Dict cache_store
        -int ttl_seconds
        +get(language, question) Optional~Dict~
        +set(language, question, response_data) None
        +clear() None
    }

    class ConnectionManager {
        -Dict~str, WebSocket~ active_connections
        -Set~WebSocket~ agent_connections
        +connect_client(session_id, websocket) None
        +disconnect_client(session_id) None
        +connect_agent(websocket) None
        +disconnect_agent(websocket) None
        +send_personal_message(message, websocket) None
        +send_to_session(session_id, message) bool
        +broadcast_to_agents(message) None
    }

    class IngestionService {
        -VectorStore vector_store
        +process_and_index_file(file_path, original_filename) int
        -_extract_text_from_pdf(path) str
        -_extract_text_from_docx(path) str
        -_chunk_text(text, chunk_size, chunk_overlap) List~str~
    }

    class MetricsService {
        -Session db
        +calculate_metrics() Dict
        -_calculate_sla_compliance() float
        -_calculate_tokens_and_costs(total_queries, cached_queries) Dict
    }

    Base <|-- Conversation
    Base <|-- Message
    Base <|-- AdminUser

    Conversation "1" *-- "many" Message : contains
    ConversationRepository ..> Conversation : manages
    ConversationRepository ..> Message : persists

    RAGService o-- VectorStore : searches
    RAGService o-- ResponseCache : optimizes
    IngestionService o-- VectorStore : indexes
    MetricsService ..> ConversationRepository : reads
```

---

## 3. Diagramas de Secuencia

### 3.1 Diagrama de Secuencia 1: Consulta RAG del Usuario (Flujo Principal)
Representa el camino que sigue un mensaje del usuario desde el navegador web hasta la respuesta generada por Groq LPU con protección de ciberseguridad y caché.

```mermaid
sequenceDiagram
    autonumber
    actor Estudiante as Estudiante (Web)
    participant UI as Widget React (FloatingChat)
    participant Sec as Capa Seguridad (Guardrails + Limiter)
    participant ChatAPI as API Endpoint (/chat)
    participant Cache as ResponseCache (RAM)
    participant RAG as RAGService
    participant Chroma as ChromaDB Vector Store
    participant Groq as Groq Cloud LPU API
    participant Repo as ConversationRepository
    participant DB as Base de Datos (SQLite/Postgres)

    Estudiante ->> UI: Escribe "¿Qué horarios hay para Francés B1?"
    UI ->> Sec: POST /api/v1/chat (Payload + API Key + IP)
    Sec ->> Sec: Validar Rate Limit (SlowAPI) y Prompt Injection (NFKD)
    alt Inyección Detectada o Bloqueo
        Sec -->> UI: 400 Bad Request / "Consulta no permitida"
        UI -->> Estudiante: Muestra alerta de seguridad
    else Consulta Válida
        Sec ->> ChatAPI: Pasar solicitud verificada
        ChatAPI ->> Repo: get_or_create_conversation(session_id)
        Repo ->> DB: INSERT / SELECT conversation
        DB -->> Repo: Objeto Conversation
        ChatAPI ->> Repo: add_message(session_id, 'user', mensaje)
        Repo ->> DB: INSERT INTO messages
        
        ChatAPI ->> Cache: get("es", pregunta)
        alt Acierto en Caché (Cache HIT)
            Cache -->> ChatAPI: Respuesta cacheada + tokens ahorrados
        else Fallo en Caché (Cache MISS)
            ChatAPI ->> RAG: answer_query(pregunta, session_id, "es")
            RAG ->> Chroma: query_similar("Francés B1 horarios", n=3)
            Chroma -->> RAG: Fragmentos oficiales del PDF curricular
            RAG ->> Groq: Prompt enriquecido con contexto oficial
            Groq -->> RAG: Respuesta generada en ~500ms
            RAG ->> Cache: set("es", pregunta, respuesta)
            RAG -->> ChatAPI: Texto generado + metadatos de tokens
        end

        ChatAPI ->> Repo: add_message(session_id, 'bot', respuesta)
        Repo ->> DB: INSERT INTO messages
        ChatAPI -->> UI: 200 OK (JSON ChatResponse)
        UI -->> Estudiante: Renderiza respuesta estilizada con badge IA
    end
```

---

### 3.2 Diagrama de Secuencia 2: Escalamiento y Chat en Vivo Bidireccional (WebSocket Handoff)
Representa la transición cuando el usuario pide un asesor, el sistema notifica por Telegram y WebSockets, un asesor toma el caso y se comunican en vivo.

```mermaid
sequenceDiagram
    autonumber
    actor Estudiante as Estudiante (Web)
    participant UI as FloatingChat Widget
    participant WS as WebSocket (/ws/chat/{session_id})
    participant WSMngr as ConnectionManager
    participant AdminAPI as Admin / Escalation API
    participant Repo as ConversationRepository
    participant n8n as Webhook n8n / Telegram
    actor AsesorTG as Asesor en Telegram
    actor AsesorWeb as Asesor en Admin Panel

    Estudiante ->> UI: "Quiero hablar con un asesor de admisiones"
    UI ->> WS: Enviar solicitud de escalamiento
    WS ->> Repo: Actualizar estado a 'pendiente'
    WS ->> n8n: POST /webhook/chat (Payload con datos del lead y sesión)
    n8n ->> AsesorTG: Alerta con botones [🙋‍♂️ Tomar Caso] [💬 WhatsApp]
    WS ->> WSMngr: broadcast_to_agents(evento 'nueva_conversacion_pendiente')
    WSMngr -->> AsesorWeb: Notificación instantánea en Inbox web

    alt Asesor Web toma el caso
        AsesorWeb ->> AdminAPI: POST /admin/conversations/{session_id}/claim
        AdminAPI ->> Repo: claim_conversation(session_id, 'CarlosAsesor')
        Repo -->> AdminAPI: Éxito (Estado transiciona a 'en_atencion')
        AdminAPI ->> WSMngr: Notificar al estudiante: "Carlos se ha conectado"
        WSMngr -->> UI: Evento 'agent_connected'
        UI -->> Estudiante: Muestra badge "Atendido por Carlos"

        AsesorWeb ->> WSMngr: Mensaje en tiempo real vía /ws/agent
        WSMngr ->> WS: Enrutar a sesión específica
        WS -->> UI: Renderizar mensaje del asesor
        
        Estudiante ->> UI: Responde "¿Tienen facilidades de pago?"
        UI ->> WS: Envía texto
        WS ->> WSMngr: Enrutar a conexiones de asesores
        WSMngr -->> AsesorWeb: Renderiza respuesta en chat en vivo
        
        AsesorWeb ->> AdminAPI: POST /admin/conversations/{session_id}/resolve
        AdminAPI ->> Repo: Marcar 'resuelto'
        AdminAPI ->> WSMngr: Notificar resolución
        WSMngr -->> UI: Evento 'conversation_resolved'
        UI -->> Estudiante: Despliega encuesta de satisfacción
    else Asesor Telegram toma el caso
        AsesorTG ->> n8n: Presiona [🙋‍♂️ Tomar Caso] (Callback query)
        n8n ->> AdminAPI: POST /admin/conversations/{session_id}/claim
        AdminAPI ->> Repo: claim_conversation(session_id, 'TelegramAdvisor')
        AdminAPI ->> WSMngr: Notificar al estudiante
        WSMngr -->> UI: "Un asesor te está atendiendo vía soporte institucional"
    end
```
