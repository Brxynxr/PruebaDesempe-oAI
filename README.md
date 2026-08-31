# Academia Lumina - Asistente de Atención al Cliente con RAG y Automatización n8n

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Groq Llama 3.3 70B](https://img.shields.io/badge/Groq-Llama_3.3_70B-orange.svg)](https://groq.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Base_Vectorial-purple.svg)](https://www.trychroma.com/)
[![n8n Automation](https://img.shields.io/badge/n8n-Router_Flujos-red.svg)](https://n8n.io/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)

Sistema completo de atención al cliente impulsado por Inteligencia Artificial para **Academia Lumina** (academia de idiomas colombiana). Utiliza **RAG (Generación Aumentada por Recuperación)** sobre documentos oficiales del negocio, orquestación con **n8n**, interfaz **React con botón flotante** y **4 niveles de ciberseguridad**.

---

## 🔑 GUÍA PASO A PASO: DÓNDE Y CÓMO CONFIGURAR LAS API KEYS

### 1. ¿Cómo obtener la API Key de Groq (Gratuita)?
1. Ingresa a la plataforma oficial de Groq en **[console.groq.com](https://console.groq.com)**.
2. Crea una cuenta gratuita o inicia sesión con tu cuenta de Google/GitHub.
3. En el menú lateral izquierdo, haz clic en **API Keys**.
4. Haz clic en el botón **Create API Key**.
5. Copia la clave generada (tendrá un formato similar a `gsk_aBc123XyZ...`).

### 2. ¿Dónde colocar la API Key de Groq y la clave de seguridad del Backend?
En el directorio `backend/`, crea un archivo llamado `.env` copiando la plantilla `.env.example`:

```bash
cd backend
cp .env.example .env
```

Abre el archivo `backend/.env` con tu editor de texto y configura las variables:

```env
# 1. Pega aquí tu API Key de Groq obtenida en console.groq.com
GROQ_API_KEY=gsk_tu_clave_real_de_groq_aqui

# 2. Clave de seguridad del backend (Utilizada para autenticar peticiones de n8n o Frontend en el header X-API-Key)
BACKEND_API_KEY=lumina_secret_key_2026

# 3. Nombre del entorno
ENVIRONMENT=development

# 4. Ruta de almacenamiento persistente de la base vectorial ChromaDB
CHROMA_DB_DIR=./chroma_data

# 5. Límite de peticiones por minuto por IP (Seguridad)
RATE_LIMIT_PER_MINUTE=10/minute

# 6. Puerto de ejecución
PORT=8000
```

---

## 1. Resumen del Problema y la Solución

### El Problema
Academia Lumina sufría de saturación en sus canales de atención (correo, WhatsApp, formulario) debido a cientos de preguntas repetitivas sobre precios, modalidades, horarios, inscripciones y certificaciones.

### La Solución Construida
1. **RAG Basado Únicamente en Documentos Oficiales**: El modelo **Llama 3.3 70B** de Groq responde basándose estrictamente en los documentos Markdown de la academia (`programas_y_precios.md`, `horarios_y_modalidades.md`, `inscripciones_y_certificaciones.md`).
2. **Escalamiento Automático a WhatsApp**: Si la pregunta está fuera de alcance (ej. intercambios culturales o becas), genera un botón directo a WhatsApp (`https://wa.me/573247836387`) y notifica al equipo interno por correo mediante n8n.
3. **4 Protecciones de Ciberseguridad**: Rate limiting (10 req/min por IP), filtro Anti Prompt-Injection, autenticación por cabecera `X-API-Key` y variables de entorno `.env`.

---

## 2. Arquitectura del Sistema

```
[ Usuario / Cliente Web ]
         │
         ▼
[ Chat Flotante React ] ──(HTTP POST + X-API-Key)──► [ Workflow Router n8n ]
                                                              │
                                                              ▼
                                                   [ Backend FastAPI ]
                                                              │
                                       ┌──────────────────────┴──────────────────────┐
                                       ▼                                             ▼
                             [ Capas de Seguridad ]                        [ Caché de Respuestas ]
                           (Rate Limit, Auth, Injection)                   (En Memoria TTL)
                                       │                                             │
                                       ▼                                             │
                             [ Base Vectorial ChromaDB ] ◄──(Búsqueda Semántica)─────┤
                                       │                                             │
                                       ▼                                             │
                             [ Groq Llama 3.3 70B ] ◄───(Síntesis RAG)──────────────┘
                                       │
                                       ▼
                       [ Verificación de Escalamiento ]
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 ▼                                           ▼
   [ Retorna Respuesta + Enlace wa.me ]     [ Envía Correo Interno en n8n ]
```

---

## 3. Instrucciones de Instalación y Ejecución

### 1. Iniciar el Backend en FastAPI
```bash
# Navegar al directorio backend
cd backend

# Crear y activar el entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar el archivo .env (Ver sección 🔑 de claves arriba)
cp .env.example .env

# Iniciar el servidor FastAPI
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```
El servidor backend se ejecutará en `http://localhost:8000` (Documentación Swagger en `http://localhost:8000/docs`).

### 2. Ejecutar Pruebas Automatizadas
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

### 4. Probar el Flujo de n8n
1. Abrir n8n -> **Workflows** -> **Import from File**.
2. Importar `n8n/workflow.json`.
3. Probar enviando una consulta vía Webhook con cURL:

```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Tienen intercambios culturales?",
    "session_id": "sesion_demo"
  }'
```

---

## 4. Referencia de Endpoints API

### `POST /api/v1/chat`
Procesa las preguntas del usuario mediante RAG y Groq.

**Cabeceras Requeridas**:
- `X-API-Key`: `lumina_secret_key_2026`
- `Content-Type`: `application/json`

**Cuerpo de la Petición**:
```json
{
  "message": "¿Cuánto cuesta el nivel A1 de inglés presencial?",
  "session_id": "sesion_web_123"
}
```

### `GET /api/v1/metrics`
Obtiene las estadísticas en tiempo real (consultas totales, tasa de escalamiento %, tasa de acierto de caché % y costos). Requiere cabecera `X-API-Key`.

### `GET /api/v1/health`
Retorna el estado de salud del backend.
