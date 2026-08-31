# Academia Lumina - AI Customer Support Assistant with RAG & n8n Automation

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Groq Llama 3.3 70B](https://img.shields.io/badge/Groq-Llama_3.3_70B-orange.svg)](https://groq.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-purple.svg)](https://www.trychroma.com/)
[![n8n Automation](https://img.shields.io/badge/n8n-Workflow_Router-red.svg)](https://n8n.io/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)

An enterprise-grade AI customer support assistant built for **Academia Lumina** (a Colombian language academy offering English, French, and Portuguese). The solution leverages **Retrieval-Augmented Generation (RAG)** over official business documents, automated workflow routing via **n8n**, a modern **React floating chat widget**, and **4 integrated cybersecurity layers**.

---

## 1. Problem & Solution Overview

### Problem Statement
Academia Lumina experienced high volumes of repetitive inquiries via digital channels regarding course pricing, class schedules, CEFR levels (A1 to C1), modalities (in-person vs. virtual), enrollment windows, and certifications. Human support teams were overwhelmed, causing delayed responses and missed registration opportunities.

### Engineered Solution
1. **Accurate Grounded AI (RAG)**: Answers customer queries strictly using official Markdown business knowledge documents (`programas_y_precios.md`, `horarios_y_modalidades.md`, `inscripciones_y_certificaciones.md`).
2. **Out-of-Scope Human Escalation**: When inquiries exceed official documentation (e.g., international cultural exchanges, sports scholarships, custom corporate deals), the assistant automatically generates a direct **WhatsApp escalation link** (`https://wa.me/573247836387`) and triggers an internal email notification to `admisiones@academialumina.co` via n8n.
3. **Robust Security**: Integrates 4 security protections from day one (Rate limiting, Anti Prompt-Injection, `X-API-Key` authentication, and `.env` secret management).
4. **Performance & Analytics**: Features in-memory TTL response caching for sub-millisecond responses on repeated queries and a dedicated `/api/v1/metrics` analytics endpoint.

---

## 2. System Architecture

```
[ User / Web Client ]
         │
         ▼
[ React Floating Chat ] ──(HTTP POST + X-API-Key)──► [ n8n Router Workflow ]
                                                              │
                                                              ▼
                                                   [ FastAPI Backend ]
                                                              │
                                       ┌──────────────────────┴──────────────────────┐
                                       ▼                                             ▼
                             [ Security Guardrails ]                       [ Response Cache ]
                           (Rate Limit, Auth, Injection)                  (In-Memory TTL)
                                       │                                             │
                                       ▼                                             │
                             [ ChromaDB Vector Store ] ◄───(Vector Search)──────────┤
                                       │                                             │
                                       ▼                                             │
                             [ Groq Llama 3.3 70B ] ◄───(RAG Synthesis)─────────────┘
                                       │
                                       ▼
                       [ Escalation Check (is_escalated) ]
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 ▼                                           ▼
   [ Return ChatResponse + wa.me ]          [ Trigger n8n Internal Email ]
```

---

## 3. Technology Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, Pydantic Settings, SlowAPI, Pytest, Uvicorn.
- **RAG & Vector Database**: ChromaDB (persistent local storage), Sentence-Transformers (`all-MiniLM-L6-v2`), Markdown section-aware chunker with overlap.
- **LLM Engine**: Groq Cloud API featuring **Llama 3.3 70B Versatile** (`temperature: 0.3`).
- **Automation & Routing**: n8n exportable workflow (`n8n/workflow.json`) with Webhook trigger and email notification node.
- **Frontend**: React 18, Vite 5, Lucide Icons, CSS Flexbox/Grid responsive floating chat widget.

---

## 4. Cybersecurity (The 4 Integrated Protections)

1. **Rate Limiting**: Enforces a strict limit of **10 requests per minute per IP address** via SlowAPI middleware.
2. **Anti Prompt-Injection Filter (`guardrails.py`)**: Inspects incoming messages against jailbreak patterns (`ignore previous instructions`, `system prompt`, `forget rules`), returning **HTTP 400 Bad Request** on attack detection.
3. **Endpoint Authentication (`security.py`)**: Validates the `X-API-Key` header against `BACKEND_API_KEY`, returning **HTTP 401 Unauthorized** if missing or invalid.
4. **Secure Secret Management**: All API keys, environment settings, and secrets are strictly loaded via `.env` and `config.py` and excluded from version control (`.gitignore`).

---

## 5. Quick Start Guide

### Prerequisites
- Python 3.12+
- Node.js v18+ & npm
- A free Groq API key from [console.groq.com](https://console.groq.com)

### Step 1: Set Up & Run Backend
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env and set your GROQ_API_KEY
# GROQ_API_KEY=gsk_your_actual_groq_key_here

# Launch FastAPI server
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```
Backend API will be running at `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).

### Step 2: Run Automated Test Suite
```bash
cd backend
PYTHONPATH=. venv/bin/pytest tests
```

### Step 3: Set Up & Run Frontend
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:3000`.

### Step 4: Import & Test n8n Workflow
1. Open n8n -> **Workflows** -> **Import from File**.
2. Select `n8n/workflow.json`.
3. Configure SMTP credentials on the email notification node.
4. Test sending a request to the webhook:

```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Do you offer cultural exchanges to Canada?",
    "session_id": "test_session_01"
  }'
```

---

## 6. API Endpoints Reference

### `POST /api/v1/chat`
Processes customer support inquiries using RAG and Groq.

**Headers**:
- `X-API-Key`: `lumina_secret_key_2026` (Required)
- `Content-Type`: `application/json`

**Request Body**:
```json
{
  "message": "¿Cuánto cuesta el nivel A1 de inglés presencial?",
  "session_id": "session_web_123"
}
```

**Response**:
```json
{
  "response": "El costo del nivel A1 de inglés en modalidad presencial es de $450.000 COP por semestre.",
  "is_escalated": false,
  "whatsapp_link": null,
  "sources": [
    {
      "content": "## Precios, Tarifas y Costos por Semestre...",
      "source": "programas_y_precios.md",
      "score": 0.85
    }
  ],
  "session_id": "session_web_123"
}
```

### `GET /api/v1/metrics`
Returns real-time analytics summary.

**Headers**: `X-API-Key` required.

**Response**:
```json
{
  "total_queries": 25,
  "cached_queries": 8,
  "escalated_queries": 3,
  "escalation_rate_percentage": "12.0%",
  "cache_hit_rate_percentage": "32.0%",
  "total_tokens_estimated": 6250,
  "estimated_cost_usd": "$0.0000 USD (Groq Free Tier)"
}
```

### `GET /api/v1/health`
Returns service status, version, and environment.

---

## 7. Project Structure

```
PruebaDesempeno/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/       # Chat, health, and metrics endpoints
│   │   │   └── router.py        # Aggregated API router
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings & env validation
│   │   │   ├── guardrails.py    # Anti prompt-injection validator
│   │   │   └── security.py      # X-API-Key auth & Rate Limiter
│   │   ├── db/
│   │   │   ├── cache.py         # ResponseCache TTL layer
│   │   │   └── vector_store.py  # ChromaDB client & semantic search
│   │   ├── services/
│   │   │   ├── ingestion_service.py # Section-aware chunking & overlap
│   │   │   ├── metrics_service.py   # Analytics & query metrics
│   │   │   └── rag_service.py       # RAG pipeline with Groq Llama 3.3 70B
│   │   ├── schemas/
│   │   │   └── chat.py          # Pydantic schemas
│   │   ├── data/                # Academia Lumina knowledge documents (.md)
│   │   └── main.py              # FastAPI application entrypoint
│   ├── tests/                   # Pytest test suite
│   ├── .env.example             # Environment template
│   └── requirements.txt         # Python dependencies
├── frontend/                    # React Vite application
├── n8n/                         # Exportable workflow.json and README_N8N.md
├── DOCUMENTACION.md             # Complete Spanish architectural documentation
└── README.md                    # Main project documentation in English
```

---

## 8. License & Author
Built for the RIWI Performance Test (Module 5.7 - AI Automation Assistant) by a Senior Full-Stack & Cybersecurity Engineer.
