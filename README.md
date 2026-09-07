# Academia Lumina AI

Sistema inteligente de soporte multilingüe y atención en vivo para **Academia Lumina** (Colombia). Combina RAG (Retrieval-Augmented Generation) con Groq LLM, chat en tiempo real vía WebSockets, automatización con Telegram/n8n y un panel administrativo integral.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite + Tailwind)            │
│   LandingPage    FloatingChat (HTTP+WS)    AdminPanel (3 tabs)  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP + WebSocket
┌──────────────────────────▼──────────────────────────────────────┐
│                    BACKEND (FastAPI - Puerto 8000)               │
│  /chat  /chat/lead  /admin/*  /metrics  /health  /ws/*          │
│  Seguridad: X-API-Key + JWT + Guardrails + Rate Limit           │
│  RAG: Groq gpt-oss-120b + ChromaDB + Gemini embeddings         │
└──────┬──────────────┬───────────────────┬───────────────────────┘
       │              │                   │
  SQLite/Postgres  ChromaDB           Telegram Bot API
  (conversaciones, (academia_lumina_kb) (notificaciones,
   mensajes, admin)                     botones interactivos)
                                         ▲
                                    n8n (4 workflows)
                                    chat, leads, SLA, reportes
```

| Servicio | Puerto | Tecnología |
| --- | --- | --- |
| Backend API | 8000 | FastAPI, Python 3.12, Uvicorn |
| Frontend SPA | 3000 | React 18, Vite 5, Tailwind v4, nginx |
| n8n | 5678 | n8nio/n8n (automatización) |

---

## Instalación

### Requisitos
- Docker Engine v24+ y Docker Compose v2.20+
- Clave API de **Groq** ([console.groq.com/keys](https://console.groq.com/keys))
- Clave API de **Google Gemini** ([aistudio.google.com](https://aistudio.google.com/))

### Pasos

```bash
git clone https://github.com/Brxynxr/PruebaDesempe-oAI.git
cd PruebaDesempe-oAI

# Configurar variables de entorno
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Editar backend/.env con tus GROQ_API_KEY y GEMINI_API_KEY

# Levantar todo
docker compose up -d --build
```

### URLs de acceso

| Servicio | URL |
| --- | --- |
| Portal Web y Chat | http://localhost:3000 |
| Panel del Asesor | http://localhost:3000/admin |
| Swagger API | http://localhost:8000/docs |
| Health Check | http://localhost:8000/api/v1/health |
| Métricas | http://localhost:8000/api/v1/metrics |
| Consola n8n | http://localhost:5678 |

### Credenciales por defecto (desarrollo)

| Credencial | Valor |
| --- | --- |
| Admin usuario | `admin` |
| Admin contraseña | `LuminaAdmin2026!` |
| X-API-Key (dev) | `lumina_dev_api_key_2026` |

> En producción, todas las credenciales se configuran como variables de entorno. Nunca usar valores de desarrollo.

### Pruebas

```bash
docker exec lumina_backend pytest -v
```
47 pruebas automatizadas (pytest + httpx).

---

## Módulos

### Backend (`backend/`)

| Capa | Archivos clave | Responsabilidad |
| --- | --- | --- |
| Core | `config.py`, `security.py`, `auth.py`, `guardrails.py` | Configuración, API key, JWT/bcrypt, anti prompt-injection |
| DB | `models.py`, `session.py`, `repository.py`, `cache.py`, `vector_store.py` | ORM (Conversation, Message, AdminUser), SQLite/PostgreSQL, caché semántica, ChromaDB |
| API | `endpoints/chat.py`, `admin.py`, `websocket.py`, `metrics.py`, `health.py` | REST + WebSocket |
| Services | `rag_service.py`, `ingestion_service.py`, `telegram_service.py`, `metrics_service.py`, `cleanup_service.py`, `connection_manager.py` | RAG+Groq, ingesta docs, Telegram omnicanal, métricas, limpieza, hub WS |

### Frontend (`frontend/`)

| Componente | Líneas | Función |
| --- | --- | --- |
| `LandingPage.jsx` | 526 | Página promocional (hero, programas, beneficios, proceso, certificación) |
| `FloatingChat.jsx` | 740 | Widget de chat flotante (HTTP + WebSocket handoff) |
| `AdminLogin.jsx` | 132 | Login JWT del portal de asesores |
| `AdminDashboard.jsx` | 1385 | Panel: Bandeja de Chats, Base RAG, Métricas y SLA |

### Automatización (`n8n/`)

| Workflow | Trigger | Función |
| --- | --- | --- |
| `workflow.json` | Webhook POST /chat | Router RAG + escalamiento Telegram con botones interactivos |
| `workflow_leads.json` | Webhook POST /leads | Notificación de leads comerciales a Telegram |
| `workflow_sla.json` | Cron cada 1 min | Supervisor SLA: alerta conversaciones pendientes >1 min |
| `workflow_reportes.json` | Cron 8:00 AM | Reporte diario de métricas a Telegram |

> Los workflows usan variables de entorno de n8n (`$env.TELEGRAM_BOT_TOKEN`, `$env.TELEGRAM_CHAT_ID`, `$env.BACKEND_API_KEY`). Configurarlas en la consola de n8n.

### Suite de pruebas (`backend/tests/`)

47 pruebas en 14 archivos: admin auth (7), cache (3), CORS (2), documents upload (3), edge cases (5), email removed, escalation lifecycle (4), health (2), metrics (3), RAG search (2), RAG service (4), rate limit (1), security (4), Telegram isolation (2).

---

## Modelo de datos

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    idioma VARCHAR(10) DEFAULT 'es' NOT NULL,
    estado VARCHAR(30) DEFAULT 'bot' NOT NULL,  -- bot|pendiente|en_atencion|resuelto
    agente_asignado VARCHAR(100),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    remitente VARCHAR(20) NOT NULL,  -- user|bot|agent
    contenido TEXT NOT NULL,
    sender_username VARCHAR(50),
    timestamp DATETIME NOT NULL
);

CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'asesor' NOT NULL,  -- admin|asesor
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

---

## Variables de entorno principales

| Variable | Descripción | Default dev |
| --- | --- | --- |
| `GROQ_API_KEY` | Clave API Groq para inferencia LLM | (requerida) |
| `GEMINI_API_KEY` | Clave API Google para embeddings | (requerida) |
| `BACKEND_API_KEY` | API key interna (frontend↔backend↔n8n) | `lumina_dev_api_key_2026` |
| `ADMIN_USERNAME` | Usuario admin inicial | `admin` |
| `ADMIN_PASSWORD` | Contraseña admin inicial | `LuminaAdmin2026!` |
| `JWT_SECRET_KEY` | Secreto para firmar JWT | (auto en dev) |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | (requerida para Telegram) |
| `TELEGRAM_CHAT_ID` | Chat ID del grupo de Telegram | (requerida para Telegram) |
| `DATABASE_URL` | URL de BD (vacío = SQLite local) | SQLite `backend/app/lumina.db` |
| `RATE_LIMIT_PER_MINUTE` | Límite de peticiones por IP | `10/minute` |

---

## Despliegue en producción (Render)

El archivo `render.yaml` configura automáticamente:
- **Backend**: servicio web Uvicorn con health check en `/api/v1/health`
- **Frontend**: servicio estático con rewrite SPA (`/ → /index.html`)
- **Base de datos**: PostgreSQL administrado `lumina-postgres`

Pasos:
1. Crear cuenta en [render.com](https://render.com)
2. Conectar el repositorio GitHub
3. Render detecta `render.yaml` y crea los servicios
4. Configurar variables de entorno sensibles en el Dashboard de Render (GROQ_API_KEY, GEMINI_API_KEY, ADMIN_PASSWORD, JWT_SECRET_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BACKEND_API_KEY)
5. Los servicios se despliegan automáticamente

---

## Estructura del proyecto

```
PruebaDesempe-oAI/
├── backend/
│   ├── app/
│   │   ├── main.py              # Bootstrap: BD, seed admin, ingestión RAG, Telegram, limpieza
│   │   ├── api/v1/endpoints/    # REST + WebSocket
│   │   ├── core/                # Config, auth, security, guardrails
│   │   ├── db/                  # ORM, sesión, repositorios, caché, vectores
│   │   ├── schemas/             # Pydantic request/response
│   │   └── services/            # RAG, ingesta, Telegram, métricas, WS, limpieza
│   ├── app/data/                # Base de conocimiento (4 documentos)
│   ├── tests/                   # 47 pruebas pytest
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Landing, Chat, Login, Dashboard
│   │   ├── services/api.js      # Cliente HTTP/WS
│   │   └── App.jsx              # Enrutado
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vite.config.js
├── n8n/                         # 4 workflows JSON
├── sena_evidencia/              # Evidencia técnica (diagramas, modelo datos, manual)
├── documents/                   # Formatos oficiales SENA
├── docker-compose.yml
├── render.yaml
└── README.md
```

---

## Créditos

- **Autor**: Breyner De Jesus Manga Arias
- **Repositorio**: [github.com/Brxynxr/PruebaDesempe-oAI](https://github.com/Brxynxr/PruebaDesempe-oAI.git)
- **Año**: 2026