# ⚙️ Backend API - Academia Lumina AI

Módulo backend desarrollado con **FastAPI (Python 3.12)**, diseñado bajo una arquitectura limpia y asíncrona para soportar atención conversacional con Inteligencia Artificial mediante RAG, ciberseguridad perimetral y canales bidireccionales en tiempo real vía WebSockets para escalamiento humano.

---

## 🏛️ Arquitectura y Responsabilidades

El backend encapsula las siguientes capacidades fundamentales:
1. **Motor RAG (Retrieval-Augmented Generation)**: Inferencia ultrarrápida impulsada por **Groq LPU** (`openai/gpt-oss-120b` y `openai/gpt-oss-20b`) sobre la base vectorial persistente en **ChromaDB**.
2. **Caché Semántico en Memoria (`cache.py`)**: Almacén con TTL (1 hora) que intercepta preguntas recurrentes para responder en <50ms y reducir a cero el consumo de tokens.
3. **Hub de WebSockets (`connection_manager.py` / `websocket.py`)**: Mantiene abiertas las sesiones de los estudiantes (`/ws/chat/{session_id}`) y las consolas de los asesores (`/ws/agent`), facilitando la transferencia fluida (Live Handoff) y la mensajería instantánea.
4. **4 Capas de Ciberseguridad**:
   - **Rate Limiting (SlowAPI)**: Sanitización de IP de cliente real contra proxys (10 req/min para usuarios públicos).
   - **Autenticación Dual**: JWT Bearer con hashing Bcrypt para asesores y cabecera `X-API-Key` para microservicios y n8n.
   - **Guardrails Semánticos (`guardrails.py`)**: Normalización Unicode NFKD y detección de Prompt Injections, jailbreaks y manipulación de roles.
   - **Sanitización PII / XSS**: Filtrado de datos confidenciales y desinfección de HTML en mensajes entrantes.
5. **Persistencia Híbrida (SQLAlchemy 2.0)**: Soporte nativo y transparente para **SQLite** (`lumina.db` local) y **PostgreSQL** (producción en la nube / Render).
6. **Ingesta Documental Multiformato (`ingestion_service.py`)**: Extracción de texto y chunking automático sobre archivos `.pdf`, `.docx`, `.md` y `.txt` con reindexación vectorial inmediata.
7. **Demonio de Auto-Limpieza (`cleanup_service.py`)**: Hilo en segundo plano que purga de la base de datos conversaciones resueltas tras 30 minutos de inactividad.

---

## 📂 Estructura de Directorios del Backend

```text
backend/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── admin.py       # Login JWT, listado de chats, claim atómico, métricas y subida de archivos
│   │   │   ├── chat.py        # Procesamiento RAG (/chat) y captura de prospectos (/lead)
│   │   │   ├── health.py      # Health checks y sondas de disponibilidad (/health)
│   │   │   ├── metrics.py     # Endpoints de reportería y cálculo de SLA (/metrics)
│   │   │   └── websocket.py   # Canales en tiempo real (/ws/chat y /ws/agent)
│   │   └── api.py             # Agrupador del router v1
│   ├── core/
│   │   ├── auth.py            # Bcrypt hashing, creación y verificación de tokens JWT
│   │   ├── config.py          # Variables de entorno tipadas con Pydantic Settings
│   │   ├── guardrails.py      # Filtro anti-inyección NFKD
│   │   └── security.py        # SlowAPI rate limiting y verificación de API Keys
│   ├── data/                  # Archivos oficiales de conocimiento (PDFs y DOCX curriculares 2026)
│   ├── db/
│   │   ├── cache.py           # Caché en memoria TTL
│   │   ├── models.py          # Modelos declarativos (Conversation, Message, AdminUser)
│   │   ├── repository.py      # Repositorio de consultas y transacciones atómicas
│   │   ├── session.py         # Fábrica de sesiones SQLAlchemy
│   │   └── vector_store.py    # Cliente persistente ChromaDB
│   ├── schemas/               # Esquemas y contratos Pydantic v2 (ChatRequest, AdminLogin, etc.)
│   ├── services/
│   │   ├── cleanup_service.py # Hilo de limpieza de tickets resueltos (>30m)
│   │   ├── connection_manager.py # Enrutamiento de WebSockets en memoria
│   │   ├── email_service.py   # Despacho de correos SMTP
│   │   ├── ingestion_service.py # Extracción de PDF/DOCX y fragmentación (chunking)
│   │   ├── metrics_service.py # Agregación estadística de SLAs, CSAT y costos
│   │   ├── rag_service.py     # Orquestador RAG con Groq LPU y fallback bilingüe
│   │   └── telegram_service.py# Bot de Telegram e integración de teclados inline
│   ├── lumina.db              # Base de datos SQLite local
│   └── main.py                # Entrada principal FastAPI y ciclo de vida (Lifespan)
├── tests/                     # 47 pruebas automatizadas con Pytest (14 módulos)
├── Dockerfile                 # Contenedor optimizado Python 3.12
└── requirements.txt           # Dependencias de producción
```

---

## 🔑 Variables de Entorno (`backend/.env`)

Copia el archivo de ejemplo para configurar tus claves:
```bash
cp .env.example .env
```

| Variable | Tipo | Descripción | Valor Local por Defecto |
| :--- | :---: | :--- | :--- |
| `GROQ_API_KEY` | Obligatoria | API Key de Groq Cloud para inferencia LLM | `gsk_...` |
| `GEMINI_API_KEY` | Obligatoria | API Key de Google Studio para embeddings | `AIzaSy...` |
| `BACKEND_API_KEY`| Obligatoria | Clave de seguridad del backend | `lumina_secret_key_2026` |
| `JWT_SECRET_KEY` | Obligatoria | Firma criptográfica de tokens JWT | `lumina_jwt_super_secret_key_2026` |
| `ADMIN_USERNAME` | Opcional | Usuario de acceso administrativo | `admin` |
| `ADMIN_PASSWORD` | Opcional | Contraseña administrativa | `LuminaAdmin2026!` |
| `DATABASE_URL` | Opcional | URL de conexión SQL (SQLite si se omite) | `sqlite:///./lumina.db` |
| `ALLOWED_ORIGINS`| Obligatoria | Orígenes CORS permitidos | `http://localhost:3000,http://127.0.0.1:3000` |
| `RATE_LIMIT_PER_MINUTE` | Opcional | Límite de peticiones por minuto por IP | `10/minute` |

---

## 🚀 Ejecución y Desarrollo Local

### Opción 1: Con Docker Compose (Recomendado)
Desde la raíz del proyecto:
```bash
docker compose up -d lumina_backend
```

### Opción 2: Entorno Virtual Python Nativo
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Documentación Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Sonda de Salud (Health)**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 🧪 Ejecución de Pruebas Automatizadas

La suite cuenta con **47 tests** de integración y unitarios:
```bash
# Dentro del contenedor:
docker exec lumina_backend pytest -v

# En entorno virtual local:
pytest -v
```
