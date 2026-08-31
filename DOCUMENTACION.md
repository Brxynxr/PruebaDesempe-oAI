# DOCUMENTACIÓN TÉCNICA Y ARQUITECTURA - ACADEMIA LUMINA

## 1. Justificación de las Decisiones de Arquitectura

### 1.1 Modelo LLM Escogido: Groq API (`openai/gpt-oss-120b`)
- **¿Por qué Groq?**: Groq utiliza procesadores LPU (Language Processing Units) diseñados específicamente para inferencia ultrarrápida, ofreciendo tiempos de respuesta de milisegundos sin requerir GPUs costosas ni hardware pesado localmente.
- **¿Por qué el modelo `openai/gpt-oss-120b`?**: Ofrece una capacidad razonada de 120 mil millones de parámetros con una fluidez natural superior en idioma español, adhiriéndose estrictamente al prompt del sistema y a las reglas anti-alucinación.

### 1.2 Estrategia RAG y Base Vectorial (ChromaDB)
- **VectorStore**: Se seleccionó **ChromaDB** por su ligera persistencia local, alto rendimiento y cero costo de licenciamiento.
- **Chunking Basado en Secciones**: La ingesta de documentos Markdown (`programas_y_precios.md`, `horarios_y_modalidades.md`, `inscripciones_y_certificaciones.md`) se realiza respetando los encabezados `#` y `##`, garantizando que las tablas de precios y horarios se conserven intactas dentro del mismo fragmento.
- **Búsqueda Semántica (`top_k=6`)**: Se configuró una ventana de contexto de 6 fragmentos recuperados por similitud de coseno, cubriendo todos los aspectos relevantes de la consulta.

### 1.3 Orquestación con n8n y Servicio de Notificaciones
- **n8n como Router Puro**: n8n actúa como orquestador no-code/low-code escuchando en `/webhook/chat`, redirigiendo las peticiones al backend FastAPI y manejando los flujos de comunicación externa.
- **EmailService Asíncrono**: Para garantizar la entrega inmediata de correos de alerta cuando ocurre un escalamiento (`is_escalated == true`), el backend ejecuta un servicio de notificaciones asíncrono hacia `breynermanga07@gmail.com`.

### 1.4 Containerización con Docker Compose
- **Aislamiento de Entornos**: Mediante `docker-compose.yml`, todos los servicios (`backend`, `n8n` y `frontend`) conviven dentro de una red privada virtual (`lumina_network`), permitiendo que n8n se comunique con el backend en `http://backend:8000/api/v1/chat` sin necesidad de IP pública ni ngrok.

---

## 2. Capas de Ciberseguridad Integradas

1. **Rate Limiting (SlowAPI)**: Limita a 10 peticiones/minuto por IP para evitar ataques de denegación de servicio (DoS).
2. **Filtro Anti Prompt-Injection (`guardrails.py`)**: Analiza la entrada del usuario mediante expresiones regulares para bloquear intentos de manipulación (*"ignore previous instructions"*).
3. **Autenticación por Cabecera (`security.py`)**: Exige la cabecera `X-API-Key` coincidente con `BACKEND_API_KEY` en los endpoints protegidos (`/chat` y `/metrics`).
4. **Gestión Estricta de Secretos**: Todas las credenciales sensibles se gestionan en `.env` y se excluyen del control de versiones.

---

## 3. Pruebas y Verificación

La suite de pruebas en Pytest (`backend/tests/`) incluye **13 pruebas unitarias e integrales** que garantizan:
- Salud del sistema (`GET /health`).
- Búsqueda vectorial adecuada en ChromaDB.
- Generación RAG correcta y escalamiento de WhatsApp.
- Bloqueo de peticiones no autenticadas o con prompt injection.
- Caché TTL de respuestas y recolección de métricas.
