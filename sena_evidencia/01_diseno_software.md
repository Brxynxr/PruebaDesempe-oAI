# 01. Documento de Diseño de Software: Academia Lumina AI

## 1. Introducción del Sistema

### 1.1 ¿Qué es Academia Lumina AI?
**Academia Lumina AI** es una plataforma integral de atención al cliente y soporte comercial automatizado de nivel empresarial, diseñada específicamente para **Academia Lumina**, una institución educativa especializada en la enseñanza de idiomas (inglés, francés, alemán, italiano y español para extranjeros) en Colombia.

El sistema combina:
1. **Inteligencia Artificial Generativa con RAG (Retrieval-Augmented Generation)**: Respuestas conversacionales instantáneas y precisas sustentadas exclusivamente en documentos oficiales de la academia (mallas curriculares, tarifas 2026, políticas de admisión, convenios y certificaciones).
2. **Transferencia en Vivo a Asesores Humanos (Live Human Handoff)**: Canales bidireccionales en tiempo real mediante WebSockets nativos que permiten a un asesor de admisiones tomar el control del chat web cuando el estudiante lo solicita o cuando el caso requiere atención especializada.
3. **Integración Omnicanal con n8n y Telegram**: Notificaciones y gestión remota de tickets desde Telegram para los asesores comerciales, con botones interactivos que permiten tomar casos, resolverlos o contactar al estudiante por WhatsApp.
4. **Portal Administrativo y de Operaciones**: Panel seguro (JWT/Bcrypt) con ingesta de documentos multiformato (PDF, DOCX, MD, TXT), métricas operativas en tiempo real (cumplimiento SLA, CSAT, latencia, ahorro de costos y tokens vía caché) y supervisión de casos.

### 1.2 ¿Para quién es el sistema? (Público Objetivo y Actores)
- **Estudiantes y Prospectos**: Usuarios del sitio web institucional que buscan información clara sobre programas académicos, precios, horarios, certificaciones oficiales o asistencia en inscripciones.
- **Asesores de Admisiones**: Personal comercial y de admisiones que atiende solicitudes complejas, gestiona prospectos calificados y atiende chats en vivo desde la interfaz web o mediante Telegram.
- **Supervisores y Administradores de TI**: Encargados de auditar la calidad del servicio, supervisar los acuerdos de nivel de servicio (SLA), cargar nueva documentación académica y analizar métricas de rendimiento.
- **Sistemas Externos y Workflows Automatizados**: Microservicios y webhooks de automatización (n8n, CRM institucional, pasarelas de notificación).

### 1.3 ¿Qué problema resuelve?
- **Respuestas desactualizadas o alucinadas**: Los chatbots tradicionales sin RAG inventan costos o normativas. Lumina AI fundamenta cada respuesta en el almacén vectorial ChromaDB con citas y contexto fidedigno.
- **Pérdida de prospectos fuera de horario de oficina**: La plataforma atiende 24/7 con IA ultrarrápida (inferencia de Groq LPU en ~300-800ms) y captura de leads.
- **Fricción en el escalamiento humano**: Cuando el bot no puede responder o el usuario solicita un asesor, el sistema no abandona al usuario; escala automáticamente a Telegram y activa un WebSocket para intervención humana inmediata.
- **Falta de trazabilidad y métricas**: Centraliza tiempos de primera respuesta, tasas de resolución autónoma y auditoría del ciclo de vida de los casos.

---

## 2. Requisitos del Sistema

### 2.1 Requisitos Funcionales (RF)

| ID | Nombre | Descripción | Módulo Responsable |
| :--- | :--- | :--- | :--- |
| **RF-01** | Consultas RAG Institucionales | El sistema debe responder preguntas sobre programas, precios, horarios y requisitos utilizando búsqueda semántica sobre documentos vectorizados en ChromaDB. | `rag_service.py`, `vector_store.py` |
| **RF-02** | Detección y Adaptación Multilingüe | El sistema debe detectar automáticamente si la consulta está en español o inglés y responder estrictamente en el mismo idioma, manteniendo coherencia contextual. | `rag_service.py`, `guardrails.py` |
| **RF-03** | Captura de Prospectos (Leads) | El sistema debe identificar datos de contacto (nombre, teléfono/WhatsApp, correo) suministrados por el usuario durante la conversación y consolidarlos como lead. | `chat.py`, `workflow_leads.json` |
| **RF-04** | Escalamiento Asistido (Live Handoff) | Si el usuario solicita un asesor humano o la consulta es inalcanzable para el bot, la conversación debe pasar a estado `pendiente` y notificar a los asesores. | `chat.py`, `repository.py`, `telegram_service.py` |
| **RF-05** | Chat Bidireccional en Vivo (WebSocket) | Debe permitir la comunicación en tiempo real entre el estudiante en la web (`/ws/chat/{session_id}`) y el asesor autenticado (`/ws/agent`). | `websocket.py`, `connection_manager.py` |
| **RF-06** | Toma Atómica de Conversaciones (Claim) | Un asesor debe reclamar explícitamente una conversación pendiente antes de enviar mensajes, evitando colisiones entre múltiples agentes. | `admin.py`, `repository.py` |
| **RF-07** | Cierre y Resolución de Casos | Tanto el asesor web como el asesor por Telegram deben poder marcar una conversación como `resuelto`, notificando al usuario y liberando el canal. | `admin.py`, `telegram_service.py`, `websocket.py` |
| **RF-08** | Ingesta de Documentación Multiformato | El administrador debe poder subir archivos `.pdf`, `.docx`, `.md` y `.txt` desde el panel web, los cuales son divididos en fragmentos (chunking) e indexados en ChromaDB de inmediato. | `admin.py`, `ingestion_service.py`, `vector_store.py` |
| **RF-09** | Gestión de Autenticación de Asesores | Acceso al panel administrativo protegido por credenciales con hash Bcrypt y emisión de tokens de sesión JWT con expiración controlada. | `auth.py`, `admin.py` |
| **RF-10** | Monitoreo y Tablero de Métricas | Debe exponer un dashboard con: tasa de resolución autónoma, casos por estado, tokens consumidos, ahorro de costos en USD por caché y métricas de latencia. | `metrics_service.py`, `metrics.py`, `AdminDashboard.jsx` |
| **RF-11** | Notificaciones y Botones en Telegram | Envío de alertas a Telegram con teclado inline: `[🙋‍♂️ Tomar Caso]`, `[✅ Caso Resuelto]`, `[💬 Abrir WhatsApp]` y `[📊 Panel Admin]`. | `telegram_service.py`, `workflow.json` |
| **RF-12** | Auto-limpieza de Sesiones Inactivas | Tarea de fondo (`CleanupService`) que elimina de la base de datos las conversaciones resueltas tras 30 minutos de inactividad para optimizar almacenamiento. | `cleanup_service.py` |

### 2.2 Requisitos No Funcionales (RNF)

| ID | Categoría | Criterio de Cumplimiento Real |
| :--- | :--- | :--- |
| **RNF-01** | **Rendimiento y Latencia** | Tiempo de inferencia LLM con Groq LPU inferior a 1.2 segundos en promedio. Respuestas cacheadas en memoria retornadas en menos de 50 milisegundos. |
| **RNF-02** | **Seguridad Perimetral (4 Capas)** | 1. Rate Limiting por IP real del cliente (SlowAPI, 10 req/min para chat público).<br>2. Autenticación dual (JWT para administradores y cabecera `X-API-Key` para microservicios).<br>3. Filtro de Prompt Injection con normalización Unicode NFKD y detección de patrones maliciosos.<br>4. Sanitización XSS y enmascaramiento de PII. |
| **RNF-03** | **Disponibilidad y Concurrencia** | Backend asíncrono con `asyncio` y FastAPI, permitiendo múltiples conexiones WebSocket concurrentes con `ConnectionManager` en memoria. |
| **RNF-04** | **Compatibilidad Multiplataforma** | Frontend adaptativo (Responsive Web Design) compatible con pantallas de escritorio, tablets y smartphones, desarrollado con React 18 y Tailwind CSS v4. |
| **RNF-05** | **Persistencia Híbrida y Portabilidad** | Compatibilidad nativa para ejecución en SQLite (desarrollo local y tests) y PostgreSQL (producción en la nube / Render) mediante SQLAlchemy 2.0 ORM. |
| **RNF-06** | **Mantenibilidad y Calidad de Código** | Suite de pruebas unitarias e integración con Pytest con 47 tests (100% pasando), cobertura sobre guardrails, ciclo de vida, RAG y autenticación. |

---

## 3. Arquitectura del Software

El sistema sigue una **Arquitectura de Microservicios Desacoplados Orientada a Servicios (SOA)** con separación estricta entre Frontend, Backend API, Base de Datos, Motor de Embeddings y Orquestador de Automatizaciones.

```mermaid
graph TD
    subgraph "Clientes y Canales"
        Student["Estudiante / Visitante Web<br>(React SPA)"]
        AdvisorWeb["Asesor de Admisiones<br>(Admin Panel Web)"]
        AdvisorTG["Asesor de Admisiones<br>(Telegram Mobile / Desktop)"]
    end

    subgraph "Frontend Layer (Port 3000)"
        Landing["Landing Page Institucional"]
        ChatWidget["FloatingChat (WebSocket + HTTP)"]
        AdminUI["AdminDashboard (SPA React + Vite)"]
    end

    subgraph "Backend API Layer (FastAPI - Port 8000)"
        Router["FastAPI API Router v1"]
        SecLayer["4 Capas de Ciberseguridad<br>(RateLimit, API Key, Guardrails, PII)"]
        WSManager["ConnectionManager<br>(WebSockets Hub)"]
        RAGCore["RAGService<br>(Groq LPU + Embeddings)"]
        CacheMngr["ResponseCache<br>(TTL Memoria)"]
        AuthMngr["Auth & JWT Service<br>(Bcrypt + PyJWT)"]
        IngestCore["IngestionService<br>(PDF, DOCX, MD, TXT)"]
        CleanCore["CleanupService<br>(Background Thread)"]
    end

    subgraph "Datos y Vector Store"
        SQLDB[("Base de Datos Relacional<br>SQLite / PostgreSQL")]
        ChromaDB[("ChromaDB Vector Store<br>Persistent Client")]
    end

    subgraph "Servicios Externos y Automatización"
        GroqAPI["Groq Cloud API<br>(gpt-oss-120b / 20b)"]
        GeminiAPI["Google Gemini API<br>(Embeddings)"]
        n8nEngine["n8n Automation Engine<br>(Port 5678)"]
        TelegramAPI["Telegram Bot API<br>(Webhooks + Long Polling)"]
        SMTPServer["Servidor SMTP<br>(Alertas por Correo)"]
    end

    Student -->|HTTP / HTTPS| Landing
    Student <-->|WebSocket /ws/chat/{id}| WSManager
    Student -->|POST /api/v1/chat| SecLayer
    
    AdvisorWeb -->|HTTP / HTTPS| AdminUI
    AdvisorWeb <-->|WebSocket /ws/agent| WSManager

    SecLayer --> Router
    Router --> RAGCore
    Router --> AuthMngr
    Router --> IngestCore
    
    RAGCore <--> CacheMngr
    RAGCore --> ChromaDB
    RAGCore --> GroqAPI
    IngestCore --> ChromaDB
    IngestCore --> GeminiAPI
    
    WSManager <--> Router
    Router <--> SQLDB
    CleanCore --> SQLDB

    Router -->|Webhook Escalamiento| n8nEngine
    n8nEngine --> TelegramAPI
    TelegramAPI <--> AdvisorTG
    AdvisorTG -->|Callbacks / Acciones| Router
    Router --> SMTPServer
```

---

## 4. Descripción de Módulos Reales del Backend

A diferencia de plantillas genéricas, cada uno de estos módulos existe físicamente en el proyecto con responsabilidades comprobadas:

### 4.1 Módulos de Servicios (`app/services/`)
- **`rag_service.py`**: Motor principal de inferencia RAG. Coordina la consulta del usuario, valida si es un cierre de conversación, verifica la caché en memoria, realiza la búsqueda de similitud en ChromaDB, construye el prompt enriquecido con contexto oficial y llama a la API de Groq Cloud. Si el LLM falla, implementa un mecanismo de contingencia (*graceful fallback*) bilingüe.
- **`connection_manager.py`**: Gestor de sockets asíncronos en memoria. Mantiene el registro de conexiones de estudiantes (`active_connections: Dict[str, WebSocket]`) y asesores (`agent_connections: Set[WebSocket]`), enrutando mensajes directos, alertas de presencia y difusiones de eventos.
- **`ingestion_service.py`**: Procesador de ingesta documental multiformato. Extrae texto crudo desde archivos `.pdf` (vía `pypdf`), `.docx` (vía `python-docx`), `.txt` y `.md`. Aplica segmentación en fragmentos (*chunking*) con superposición (*overlap*) y genera metadatos para indexación.
- **`cleanup_service.py`**: Demonio en segundo plano que ejecuta cada 10 minutos una limpieza en la base de datos eliminando registros de conversaciones en estado `resuelto` cuya última actualización exceda los 30 minutos.
- **`metrics_service.py`**: Motor de agregación analítica. Calcula métricas de rendimiento operacional: CSAT estimado, tasa de resolución autónoma del bot, costo ahorrado en USD (calculado a $0.0005 por token de entrada y $0.0015 por token de salida evitados gracias a la caché), latencias y distribución por idiomas.
- **`telegram_service.py`**: Integración bidireccional con Telegram. Formatea mensajes con datos del estudiante, genera teclados inline (`InlineKeyboardMarkup`) con botones de acción y gestiona las respuestas de los asesores directamente en el chat grupal o privado.
- **`email_service.py`**: Servicio asíncrono para despacho de correos electrónicos vía SMTP ante eventos de escalamiento o reportes diarios.

### 4.2 Módulos de Núcleo y Seguridad (`app/core/`)
- **`guardrails.py`**: Filtro de ciberseguridad semántica. Aplica normalización Unicode NFKD para evitar evasiones por homoglifos, analiza patrones de *Prompt Injection*, *Jailbreak*, manipulación de roles ("System Prompt Override") e intentos de exfiltración de credenciales.
- **`security.py`**: Configuración perimetral de SlowAPI (Rate Limiter) basado en la IP real del cliente (limpiando cabeceras `X-Forwarded-For`), y verificación obligatoria de cabeceras `X-API-Key`.
- **`auth.py`**: Seguridad de identidad administrativa. Encriptación de contraseñas mediante algoritmo Bcrypt (`passlib`), creación y verificación de tokens JWT con algoritmo HS256 y esquemas Bearer de FastAPI.
- **`config.py`**: Gestión centralizada de variables de entorno mediante `pydantic-settings.BaseSettings`, con tipado estricto y valores por defecto seguros.

### 4.3 Módulos de Base de Datos y Persistencia (`app/db/`)
- **`models.py`**: Definición de modelos declarativos SQLAlchemy 2.0 (`Conversation`, `Message`, `AdminUser`).
- **`repository.py`**: Patrón Repositorio (`ConversationRepository`). Encapsula todas las operaciones transaccionales de lectura y escritura: creación de sesiones, agregado de mensajes, transiciones de estado y toma atómica de casos con control de concurrencia.
- **`vector_store.py`**: Interfaz con ChromaDB. Gestiona la colección vectorial persistente `lumina_knowledge_base`, inicializa el cliente Chroma y ejecuta consultas por similitud de cosenos.
- **`cache.py`**: Caché semántica en memoria (`ResponseCache`) con políticas TTL (Time-To-Live de 1 hora) y clave hash normalizada por idioma e intención.
- **`session.py`**: Fábrica de sesiones de base de datos (`sessionmaker`) con soporte dinámico para SQLite (`sqlite:///./lumina.db`) y PostgreSQL (`postgresql://...`).

---

## 5. Justificación Técnica de Decisiones Clave

| Decisión Arquitectónica | Tecnología Seleccionada | Justificación y Alternativas Descartadas |
| :--- | :--- | :--- |
| **Framework Backend** | **FastAPI (Python 3.12)** | Proporciona soporte asíncrono nativo para WebSockets y concurrencia alta, tipado estricto con Pydantic v2 y documentación interactiva OpenAPI/Swagger automática. *Descartados: Flask (sincrónico, bajo rendimiento con WebSockets) y Django (demasiado pesado para una arquitectura API desacoplada).* |
| **Motor de Inferencia LLM** | **Groq LPU (`gpt-oss-120b` / `20b`)** | Velocidades de generación de tokens sin precedentes (inferencia completa en ~300-800ms vs 3000-5000ms de OpenAI/Anthropic estándar), fundamental para una experiencia de chat conversacional sin esperas frustrantes para el usuario. |
| **Base de Datos Vectorial** | **ChromaDB (Persistent)** | Vector store ligero, de código abierto, sin dependencias externas pesadas ni costos mensuales de infraestructura. Se ejecuta embebido con persistencia en disco local y permite re-indexación instantánea. *Descartados: Pinecone (costos recurrentes y dependencia de red externa).* |
| **Base de Datos Relacional** | **SQLAlchemy 2.0 (SQLite / PostgreSQL)** | Arquitectura desacoplada de almacenamiento. Permite desarrollo y pruebas locales con SQLite (`lumina.db`) en cero configuración, y migración transparente a PostgreSQL en Render mediante cambio de variable `DATABASE_URL`. |
| **Capa de Frontend** | **React 18 + Vite 5 + Tailwind CSS v4** | Tiempos de compilación ultrarrápidos (build de producción en ~2.8s), bundle liviano (~237KB gzip), reactividad para estados complejos de chat y diseño visual moderno con Tailwind v4 sin necesidad de librerías CSS pesadas. |
| **Orquestación de Flujos** | **n8n Automation Engine** | Facilita la automatización visual de integraciones con Telegram, CRMs y cron jobs sin acoplar lógica no comercial en el núcleo de FastAPI. Los flujos se versionan como JSON declarativos. |
