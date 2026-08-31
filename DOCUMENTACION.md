# Documentación Técnica Completa del Proyecto - Academia Lumina AI Assistant

## 1. Contexto del Proyecto y Caso de Uso (RIWI Módulo 5.7)

### El Problema
**Academia Lumina** es una academia de idiomas colombiana que ofrece cursos de Inglés, Francés y Portugués en modalidades presencial y virtual. El equipo de atención al cliente y admisiones se encontraba saturado por un alto volumen de preguntas repetitivas a través de canales digitales (horarios, tarifas por semestre, niveles disponibles, requisitos de inscripción y certificación). Esto generaba demoras en la respuesta, pérdida de oportunidades de inscripción y costos operativos elevados.

### La Solución
Se construyó un **Asistente Virtual de Atención al Cliente impulsado por Inteligencia Artificial (RAG)** y automatizado mediante **n8n**. El asistente:
- Responde automáticamente consultas basándose **únicamente** en los documentos oficiales del negocio.
- Detecta cuando una pregunta supera el alcance de la documentación oficial (por ejemplo: intercambios al exterior o convenios a medida) y deriva al usuario inmediatamente a un asesor humano mediante un enlace directo a **WhatsApp** (`+57 324 783 6387`) y una notificación por correo electrónico.
- Protege la API con 4 niveles de ciberseguridad.
- Mantiene el tono de marca cercano y amigable de la academia y es eficiente en costos.

---

## 2. Justificación del Stack Tecnológico Seleccionado

| Área / Componente | Tecnología Seleccionada | Justificación y Finalidad Técnica |
|---|---|---|
| **Backend Framework** | **Python + FastAPI** | Seleccionado por su alto rendimiento asíncrono, validación nativa de esquemas con Pydantic, generación automática de documentación OpenAPI y excelente integración con el ecosistema de IA y bases de datos vectoriales. |
| **Modelo de Lenguaje (LLM)** | **Groq (Llama 3.3 70B)** | Elegido para sustituir APIs de pago por un modelo de 70 mil millones de parámetros de código abierto (Meta) ejecutado en la nube ultra-rápida de Groq. Ofrece respuesta en menos de 1 segundo, cero costo en inferencia y compatibilidad nativa con la API de OpenAI. |
| **Base de Datos Vectorial** | **ChromaDB** | Base de datos vectorial persistente e idónea para RAG en Python. No requiere servidores externos complejos, se almacena localmente en `./chroma_data` y realiza búsquedas por similitud semántica con la librería `sentence-transformers` (`all-MiniLM-L6-v2`). |
| **Orquestador y Router** | **n8n** | Utilizado en rol de **Router Puro**. Recibe la solicitud vía Webhook (`POST /webhook/chat`), la reenvía a FastAPI y, si la respuesta requiere escalamiento (`is_escalated == true`), dispara el envío de correos internos al equipo de admisiones (`admisiones@academialumina.co`). |
| **Frontend** | **React + Vite** | Interfaz moderna que simula la landing page de la academia con un botón flotante desplegable estilo Intercom. Ofrece soporte dinámico para botones de WhatsApp cuando se activa un escalamiento. |
| **Seguridad** | **SlowAPI + Guardrails + API Key** | Proporciona 4 niveles de protección: Rate Limiting (10 req/min/IP), validación anti-prompt injection, autenticación por cabecera `X-API-Key` y variables de entorno `.env`. |

---

## 3. Desglose Detallado por Fases de Desarrollo

### Fase 0 — Arquitectura y Planificación
- **Qué se hizo**: Se diseñó la estructura de carpetas desacoplada (`backend/`, `frontend/`, `n8n/`) y se definieron los requerimientos de seguridad, dominio de negocio y enlaces de contacto.
- **Por qué**: Para establecer límites claros entre capas (capa de API, capa de servicios RAG, capa de almacenamiento vectorial y capas de presentación).

### Fase 1 — Backend Base con FastAPI
- **Qué se hizo**: Creación de `main.py`, rutas agrupadas `/api/v1`, Pydantic Settings (`config.py`), esquemas de datos (`schemas/chat.py`) y endpoint `/health`.
- **Por qué**: Garantizar que el backend levante con tipado estricto, variables de entorno validadas desde el arranque y pruebas unitarias basales de salud.

### Fase 2 — Ingesta y RAG aislados
- **Qué se hizo**:
  1. Elaboración de los 3 documentos Markdown de conocimiento (`programas_y_precios.md`, `horarios_y_modalidades.md`, `inscripciones_y_certificaciones.md`).
  2. Implementación de `IngestionService` con fragmentación (*chunking*) inteligente respetando encabezados Markdown (`#` / `##`) y solapamiento (*overlap*) de caracteres.
  3. Creación de `VectorStore` encapsulando ChromaDB persistente en disco.
  4. Ingesta automática mediante el handler `lifespan` de FastAPI.
- **Por qué**: Mantener bloques semánticos y tablas de precios integras dentro de un mismo fragmento evita que la información de tarifas quede dividida al buscar por similitud semántica.

### Fase 3 — Integración con Groq Llama 3.3 70B y Prompt Engineering
- **Qué se hizo**: Desarrollado `RAGService` e implementado el System Prompt del asistente.
- **Detalle de Prompt Engineering**:
  - **Rol**: Asistente virtual amigable y servicial de Academia Lumina.
  - **Regla Estricta Anti-Alucinación**: Prohibición explícita de responder sobre información ausente en el contexto de negocio.
  - **3 Ejemplos Few-Shot**:
    1. Pregunta directa en alcance (precio exacto $450.000 presencial / $380.000 virtual).
    2. Pregunta ambigua pero resoluble (niveles A1 a C1 en francés).
    3. Pregunta fuera de alcance (intercambios culturales -> respuesta formal + link a WhatsApp `https://wa.me/573247836387`).

### Fase 4 — Integración de las 4 Protecciones de Seguridad
- **Qué se hizo**:
  1. **Rate Limiting**: Configurado `slowapi` limitando las solicitudes a 10 req/min por dirección IP.
  2. **Validación Anti Prompt-Injection (`guardrails.py`)**: Analiza la entrada del usuario mediante expresiones regulares para bloquear ataques de jailbreak (`ignore instructions`, `system prompt`, `olvida las instrucciones`) devolviendo HTTP 400.
  3. **Autenticación por Header (`security.py`)**: Exige la cabecera `X-API-Key` devolviendo HTTP 401 si falta o no coincide con `.env`.
  4. **Gestión de Secretos**: Todas las credenciales en `.env` y excluidas en `.gitignore`.

### Fase 5 — Flujo de n8n (Router y Notificación)
- **Qué se hizo**: Generación de `n8n/workflow.json` y `n8n/README_N8N.md`.
- **Por qué**: n8n actúa como Router Puro recibiendo el Webhook, invocando a FastAPI con `X-API-Key` y enviando una alerta por correo a `admisiones@academialumina.co` cuando la consulta es escalada a humano.

### Fase 6 — Frontend React
- **Qué se hizo**: Aplicación en React + Vite que renderiza la landing page de la academia y un botón flotante estilo Intercom.
- **Por qué**: Brinda una experiencia de usuario realista y profesional donde el usuario puede interactuar con el chat y dar clic en el botón de WhatsApp cuando se activa un escalamiento.

### Fase 7 — Caché y Métricas
- **Qué se hizo**:
  1. **`ResponseCache`**: Caché TTL en memoria para servir respuestas frecuentes en ~1ms.
  2. **`MetricsService`**: Monitoreo de consultas totales, respuestas cacheadas, escalamientos, tasa de escalamiento (%) y costo acumulado ($ USD).
  3. **Endpoint `GET /api/v1/metrics`**: API protegida para auditar el desempeño del sistema.

---

## 4. Guía de Ejecución y Pruebas

### Requisitos Previos
- Python 3.12+
- Node.js v18+ y npm

### 1. Iniciar el Backend FastAPI
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### 2. Ejecutar Pruebas Automatizadas
```bash
cd backend
PYTHONPATH=. venv/bin/pytest tests
```

### 3. Iniciar el Frontend React
```bash
cd frontend
npm install
npm run dev
```
Acceder en el navegador a `http://localhost:3000`.

### 4. Probar el Workflow de n8n
Importar `n8n/workflow.json` en tu instancia de n8n y enviar una petición de prueba:
```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Hacen intercambios culturales?",
    "session_id": "demo_n8n"
  }'
```
