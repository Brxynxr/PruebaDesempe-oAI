# Academia Lumina - Asistente de Atención al Cliente con RAG, Docker y n8n

[![Docker Compose](https://img.shields.io/badge/Docker_Compose-Soporte_Total-blue.svg)](https://www.docker.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Groq LLM](https://img.shields.io/badge/Groq-openai%2Fgpt--oss--120b-orange.svg)](https://groq.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Base_Vectorial-purple.svg)](https://www.trychroma.com/)
[![n8n Automation](https://img.shields.io/badge/n8n-Router_Flujos-red.svg)](https://n8n.io/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)

Sistema completo de atención al cliente impulsado por Inteligencia Artificial para **Academia Lumina** (academia de idiomas colombiana). Utiliza **RAG (Generación Aumentada por Recuperación)** sobre documentos oficiales del negocio, orquestación con **n8n**, interfaz **React con botón flotante de WhatsApp** y **4 niveles de ciberseguridad**.

---

## 🔑 GUÍA RÁPIDA DE CONFIGURACIÓN DE API KEYS

### 1. ¿Cómo obtener la API Key de Groq (Gratuita)?
1. Ingresa a la plataforma oficial de Groq en **[console.groq.com](https://console.groq.com)**.
2. Crea una cuenta gratuita o inicia sesión con tu cuenta de Google/GitHub.
3. En el menú lateral izquierdo, haz clic en **API Keys**.
4. Haz clic en el botón **Create API Key**.
5. Copia la clave generada (tendrá un formato similar a `gsk_aBc123XyZ...`).

### 2. ¿Dónde colocar la API Key de Groq?
En el directorio `backend/`, crea un archivo llamado `.env` copiando la plantilla `.env.example`:

```bash
cd backend
cp .env.example .env
```

Abre el archivo `backend/.env` con tu editor de texto y configura tu clave:

```env
GROQ_API_KEY=gsk_tu_clave_real_de_groq_aqui
BACKEND_API_KEY=lumina_secret_key_2026
ENVIRONMENT=development
CHROMA_DB_DIR=./chroma_data
RATE_LIMIT_PER_MINUTE=10/minute
PORT=8000
```

---

## 🚀 OPCIÓN 1: EJECUCIÓN RÁPIDA CON DOCKER (RECOMENDADA)

Para desplegar y ejecutar todo el ecosistema (Backend, Frontend y n8n) en contenedores aislados con un solo comando:

```bash
docker compose up -d --build
```

### URLs de los Servicios al Containerizar:
- 🌐 **Frontend Web (React + Nginx)**: [http://localhost:3000](http://localhost:3000)
- ⚡ **Backend FastAPI (RAG + Swagger Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 🔴 **n8n Local (Workflow Conectado)**: [http://localhost:5678](http://localhost:5678)

> **Nota**: En la red interna de Docker, n8n se comunica directamente con el backend mediante `http://backend:8000/api/v1/chat` sin requerir ngrok ni túneles externos.

---

## 💻 OPCIÓN 2: EJECUCIÓN MANUAL LOCAL (SIN DOCKER)

### 1. Iniciar el Backend en FastAPI
```bash
# Navegar al directorio backend
cd backend

# Crear y activar el entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servidor FastAPI
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### 2. Ejecutar Pruebas Automatizadas (Pytest)
```bash
cd backend
PYTHONPATH=. venv/bin/pytest tests
```

### 3. Iniciar el Frontend en React
```bash
cd frontend
npm install
npm run dev
```
Acceder en el navegador a `http://localhost:3000`.

---

## 📑 ESTRUCTURA DEL PROYECTO

```
.
├── backend/                  # Código fuente de la API FastAPI y RAG
│   ├── app/
│   │   ├── api/              # Endpoints (/chat, /metrics, /health)
│   │   ├── core/             # Configuración, Seguridad y Guardrails
│   │   ├── data/             # Documentos Markdown base para el RAG
│   │   ├── db/               # VectorStore (ChromaDB) y Cache TTL
│   │   ├── schemas/          # Modelos Pydantic
│   │   └── services/         # RAGService, IngestionService, EmailService, MetricsService
│   ├── tests/                # Suite de 13 pruebas automatizadas con Pytest
│   ├── Dockerfile            # Configuración Docker del Backend
│   └── requirements.txt      # Dependencias Python
├── frontend/                 # Aplicación Web React con Vite y Tailwind
│   ├── src/                  # Componentes (FloatingChat.jsx) y estilos
│   └── Dockerfile            # Configuración Docker Nginx del Frontend
├── n8n/                      # Orquestador de Flujos
│   ├── workflow.json         # Flujo exportable de 5 nodos para n8n
│   └── README_N8N.md         # Guía de importación de n8n
├── docker-compose.yml        # Orquestación global con Docker Compose
├── DOCUMENTACION.md          # Documentación detallada del proyecto en español
└── README.md                 # Guía rápida de uso
```

---

## 🛡️ CIBERSEGURIDAD Y PROTECCIÓN

El sistema cuenta con **4 niveles de ciberseguridad activa**:
1. **Rate Limiting**: Máximo 10 peticiones/minuto por dirección IP (SlowAPI).
2. **Filtro Anti Prompt-Injection**: Bloquea intentos de jailbreak y manipulación de instrucciones.
3. **Autenticación por Cabecera**: Requiere la clave `X-API-Key: lumina_secret_key_2026` para consumir la API.
4. **Almacenamiento Seguro**: Manejo estricto de secretos y claves mediante `.env`.
