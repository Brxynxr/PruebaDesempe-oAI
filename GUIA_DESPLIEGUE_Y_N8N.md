# 🚀 Guía Integral de Despliegue y Configuración de n8n — Academia Lumina AI

Esta guía detalla paso a paso el proceso completo para levantar el ecosistema de **Academia Lumina AI** (Backend FastAPI, Frontend React, Base Vectorial ChromaDB, Persistencia SQLite y Automatización n8n), así como la configuración e importación de los flujos de trabajo en **n8n**.

---

## 📋 1. Requisitos Previos

Antes de iniciar, asegúrate de contar con las siguientes herramientas instaladas en tu sistema:

* **Docker** (versión 24.0 o superior) y **Docker Compose** (v2 o superior) — *Recomendado para despliegue estándar.*
* **Git** para clonar y gestionar el repositorio.
* *(Opcional para desarrollo local sin Docker)*:
  * **Python 3.10+** (Recomendado 3.11 / 3.12).
  * **Node.js 18+** y **npm** (v9+).
* **API Keys necesarias**:
  * **Groq API Key**: Para inferencia ultra-rápida del LLM ([Obtener en Groq Console](https://console.groq.com/keys)).
  * **Google Gemini API Key**: Para la generación de embeddings multilingües con `gemini-embedding-001` ([Obtener en Google AI Studio](https://aistudio.google.com/app/apikey)).

---

## 🏗️ 2. Arquitectura de Servicios y Puertos

El proyecto se compone de 3 servicios orquestados mediante Docker Compose:

| Servicio | Tecnología | Puerto Local | Descripción |
| :--- | :--- | :--- | :--- |
| **`backend`** | FastAPI / Python 3.12 | `8000` | API RAG, ChromaDB, SQLite, WebSockets y Autenticación JWT |
| **`frontend`** | React + Vite + Nginx | `3000` | Portal público de estudiantes y Panel Administrativo de Asesores |
| **`n8n`** | n8n Container | `5678` | Motor de automatización, webhooks y tareas programadas (Cron) |

---

## ⚙️ 3. Configuración de Variables de Entorno

El proyecto utiliza variables de entorno separadas para backend y frontend.

### 3.1 Configuración del Backend (`backend/.env`)

Copia la plantilla de ejemplo o crea el archivo `backend/.env`:

```bash
cd backend
cp .env.example .env
```

Edita `backend/.env` con tus credenciales reales:

```env
# ==============================================================================
# CONFIGURACIÓN GENERAL DEL BACKEND
# ==============================================================================
APP_NAME="Academia Lumina AI Assistant"
VERSION="2.0.0"
ENVIRONMENT="development"
PORT=8000

# ==============================================================================
# SEGURIDAD Y CLAVES DE API
# ==============================================================================
# Clave(s) de Groq para inferencia. Puedes colocar una sola o varias separadas por coma para rotación automática
GROQ_API_KEY=gsk_tu_clave_de_groq_aqui
GROQ_API_KEYS=gsk_tu_clave_de_groq_aqui

# Clave de Google Gemini para embeddings de alta precisión (gemini-embedding-001)
GEMINI_API_KEY=AIzaSy_tu_clave_de_gemini_aqui

# API Key interna para comunicación segura entre microservicios / n8n / endpoints protegidos
BACKEND_API_KEY=lumina_dev_api_key_2026

# Orígenes CORS permitidos (separados por coma)
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000

# Límite de peticiones por minuto por IP (SlowAPI)
RATE_LIMIT_PER_MINUTE=20/minute

# ==============================================================================
# BASE DE DATOS Y VECTOR STORE
# ==============================================================================
# Directorio persistente para la base vectorial ChromaDB
CHROMA_DB_DIR=./chroma_data

# URL de conexión a la base de datos relacional (SQLite por defecto, o PostgreSQL en Render)
# Ejemplo SQLite: sqlite:///lumina.db
# Ejemplo PostgreSQL: postgresql://user:pass@host:5432/dbname
DATABASE_URL=sqlite:///lumina.db

# ==============================================================================
# AUTENTICACIÓN ADMINISTRATIVA (PANEL DE ASESORES & JWT)
# ==============================================================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_SECRET_KEY=lumina_jwt_super_secret_key_change_in_production_2026
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# ==============================================================================
# PARÁMETROS DE ATENCIÓN Y CONTACTO HUMANO
# ==============================================================================
ADVISOR_NAME="Asesor de Admisiones"
WHATSAPP_NUMBER="+57 300 000 0000"
WHATSAPP_URL="https://wa.me/573000000000"
ESCALATION_EMAIL="admissions@academialumina.edu.co"

# ==============================================================================
# CONFIGURACIÓN SMTP (NOTIFICACIONES DE LEADS Y ALERTAS)
# ==============================================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_app_password_de_gmail
SMTP_USE_TLS=true
SMTP_SENDER_EMAIL=tu_correo@gmail.com

# ==============================================================================
# INTEGRACIÓN OMNICANAL TELEGRAM (BOT DE ESCALAMIENTO Y ATENCIÓN EN VIVO)
# ==============================================================================
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=-1001234567890
```

> [!TIP]
> **Integración con Telegram:**
> 1. Crea un bot con `@BotFather` en Telegram y obtén tu `TELEGRAM_BOT_TOKEN`.
> 2. Agrega el bot a tu grupo de asesores o inicia chat privado y obtén el `TELEGRAM_CHAT_ID`.
> 3. El bot enviará alertas estructuradas con la duda no resuelta, nombre y WhatsApp del estudiante, y botones interactivos: `[🙋‍♂️ Tomar Caso]` y `[✅ Caso Resuelto]`.
> 4. Los casos resueltos cuentan con auto-limpieza periódica de **30 minutos** mediante el servicio `CleanupService`.

> [!TIP]
> Si no cuentas con credenciales SMTP activas, el backend registrará los intentos de envío en los logs de consola sin bloquear la interacción del estudiante ni el escalamiento en la base de datos.

---

### 3.2 Configuración del Frontend (`frontend/.env`)

Crea o edita el archivo `frontend/.env`:

```bash
cd frontend
cp .env.example .env
```

Contenido de `frontend/.env`:

```env
# URL base del Backend FastAPI
VITE_BACKEND_URL=http://localhost:8000

# Clave de autenticación API para el frontend
VITE_BACKEND_API_KEY=lumina_dev_api_key_2026
```

---

## 🐳 4. Levantamiento del Proyecto con Docker Compose (Método Recomendado)

Desde la raíz del repositorio, ejecuta:

```bash
# 1. Construir las imágenes y levantar los contenedores en segundo plano
docker compose up -d --build

# 2. Verificar el estado de los contenedores
docker compose ps
```

Deberás ver los tres contenedores en estado **Up / Healthy**:

```text
NAME                IMAGE                     COMMAND                  SERVICE    STATUS
lumina_backend      pruebadesempe-oai-backend "uvicorn app.main:app…"  backend    running (healthy)
lumina_frontend     pruebadesempe-oai-frontend "nginx -g 'daemon of…"  frontend   running
lumina_n8n          n8nio/n8n:latest          "tini -- /docker-ent…"   n8n        running
```

### Verificación de URLs activas:

* 🌐 **Portal del Estudiante (Frontend Web):** [http://localhost:3000](http://localhost:3000)
* 🎧 **Panel Administrativo & Bandeja en Vivo:** [http://localhost:3000/admin/login](http://localhost:3000/admin/login)
  * *Usuario:* `admin`
  * *Contraseña:* `admin123` *(configurable en `.env`)*
* 📚 **Documentación Interactiva Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)
* 📊 **Endpoint de Métricas en Vivo:** [http://localhost:8000/api/v1/metrics](http://localhost:8000/api/v1/metrics)
* ⚙️ **Consola de Automatización n8n:** [http://localhost:5678](http://localhost:5678)

---

## 💻 5. Levantamiento Alternativo (Desarrollo Local sin Docker)

Si prefieres ejecutar los servicios directamente en tu entorno local:

### Terminal 1: Backend FastAPI

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scriptsctivate
pip install -r requirements.txt

# Ejecutar el servidor con hot-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Frontend React + Vite

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

---

## ⚡ 6. Configuración e Importación Paso a Paso en n8n

El directorio `n8n/` incluye **3 flujos de trabajo independientes** que cubren la automatización omnicanal:

1. **`workflow.json`**: Enrutador Webhook para recibir consultas de canales externos, consultar el RAG de FastAPI y disparar alertas de escalamiento si se requiere.
2. **`workflow_sla.json`**: Cron cada 5 minutos que detecta conversaciones en espera de asesor humano que superen 10 minutos de inactividad.
3. **`workflow_reportes.json`**: Cron diario (8:00 AM) que recopila las métricas del sistema, consumo de tokens y costos estimados en USD, enviando un digest por correo a supervisores.

---

### Paso 6.1: Primer Ingreso a n8n

1. Abre en tu navegador: [http://localhost:5678](http://localhost:5678).
2. Si es tu primera vez, n8n te solicitará crear una cuenta de administrador local (Nombre, Email y Contraseña). Completa el registro.
3. Llegarás al **Canvas Principal de n8n**.

---

### Paso 6.2: Importación de los 3 Workflows

Repite los siguientes pasos para cada uno de los 3 archivos JSON ubicados en la carpeta `n8n/`:

#### Workflow 1: Router de Consultas y Escalamiento (`workflow.json`)
1. En el menú lateral izquierdo, haz clic en **Workflows** y luego en **Add Workflow** (o botón `+` arriba a la derecha).
2. Haz clic en el botón de opciones `...` (arriba a la derecha del lienzo) y selecciona **Import from File**.
3. Selecciona el archivo `n8n/workflow.json` desde tu explorador de archivos.
4. Verás los nodos conectados:
   * **Webhook - Recepción de Consulta**: Endpoint `POST /webhook/chat`.
   * **HTTP Request - Router FastAPI RAG**: Envía la consulta a `http://backend:8000/api/v1/chat`.
   * **¿Requiere Escalamiento? (IF Node)**: Evalúa si `is_escalated == true`.
   * **Notificación Correo Interno**: Envía alerta por email si escaló.
   * **Respond to Webhook**: Retorna el JSON estructurado al emisor original.
5. Haz clic en **Save** y luego activa el switch **Active / Published** (arriba a la derecha).

---

#### Workflow 2: Monitor de SLA de Atención Humana (`workflow_sla.json`)
1. Crea un nuevo workflow (`+ New Workflow`).
2. Haz clic en `...` -> **Import from File** y selecciona `n8n/workflow_sla.json`.
3. Verás los nodos:
   * **Schedule Trigger (Cron)**: Dispara cada 5 minutos.
   * **Consultar SLA Breached en Backend**: Ejecuta `GET http://backend:8000/api/v1/admin/conversations/sla/breached?threshold_minutes=10` con cabecera `X-API-Key: {{ $env.BACKEND_API_KEY }}`.
   * **¿Hay Conversaciones con SLA Incumplido?**: Verifica si la lista contiene elementos (`length > 0`).
   * **Alerta Email Supervisores**: Envía correo con la lista de sesiones que llevan más de 10 minutos esperando.
4. Haz clic en **Save** y activa el interruptor **Active / Published**.

---

#### Workflow 3: Reporte Diario Ejecutivo de Métricas (`workflow_reportes.json`)
1. Crea un nuevo workflow (`+ New Workflow`).
2. Haz clic en `...` -> **Import from File** y selecciona `n8n/workflow_reportes.json`.
3. Verás los nodos:
   * **Schedule Trigger**: Dispara todos los días a las **8:00 AM** (Zona horaria `America/Bogota`).
   * **Consultar Métricas en Backend**: Ejecuta `GET http://backend:8000/api/v1/metrics` con cabecera `X-API-Key`.
   * **Construir y Enviar Reporte Ejecutivo**: Construye el informe con total de consultas, tasa de caché, tokens reales consumidos y costos acumulados en USD.
4. Haz clic en **Save** y activa el interruptor **Active / Published**.

---

### Paso 6.3: Configuración de Credenciales SMTP en n8n

Para que los nodos de correo (`emailSend`) de los 3 workflows envíen emails reales:

1. En el menú lateral izquierdo de n8n, ve a **Credentials** -> **New Credential**.
2. Busca y selecciona **SMTP**.
3. Ingresa los datos de tu servidor de correo:
   * **User:** `tu_correo@gmail.com`
   * **Password:** `tu_contraseña_o_app_password`
   * **Host:** `smtp.gmail.com`
   * **Port:** `587`
   * **SSL/TLS:** `STARTTLS`
4. Guarda las credenciales y selecciónalas en los nodos de envío de email de cada workflow.

---

## 🧪 7. Verificación y Pruebas End-to-End

### 7.1 Prueba del Webhook de n8n con cURL

Prueba que el flujo completo de n8n recibe la consulta y dialoga con el backend de FastAPI:

```bash
curl -X POST http://localhost:5678/webhook/chat   -H "Content-Type: application/json"   -d '{
    "message": "¿Qué horarios tienen disponibles para el curso de inglés?",
    "session_id": "test_n8n_estudiante_01"
  }'
```

**Respuesta esperada:**
```json
{
  "response": "Ofrecemos diferentes horarios según la modalidad...",
  "is_escalated": false,
  "whatsapp_link": null,
  "session_id": "test_n8n_estudiante_01"
}
```

---

### 7.2 Prueba de Escalamiento Vía n8n

Envía una consulta que deba escalar a un humano (ej. solicitud de reembolso):

```bash
curl -X POST http://localhost:5678/webhook/chat   -H "Content-Type: application/json"   -d '{
    "message": "Me cobraron dos veces la matrícula, necesito devolución de mi dinero",
    "session_id": "test_n8n_reclamo_02"
  }'
```

**Respuesta esperada:**
```json
{
  "response": "Lamento mucho el inconveniente con tu pago. Para revisar tu caso de inmediato y gestionar la solución, te voy a conectar con un asesor humano de admisiones.",
  "is_escalated": true,
  "whatsapp_link": "https://wa.me/573000000000?text=...",
  "session_id": "test_n8n_reclamo_02"
}
```

*Verifica que en el panel de n8n el nodo de notificación por email se haya ejecutado exitosamente.*

---

### 7.3 Ejecución de la Suite Completa de Tests Automatizados

Para verificar que todos los componentes (Seguridad, RAG, WebSockets, JWT y Métricas) están 100% operativos:

```bash
# Dentro del contenedor Docker
docker exec -it lumina_backend pytest backend/tests -v

# O en entorno local con venv
PYTHONPATH=backend pytest backend/tests -v
```

Deberás obtener: **`43 passed in X.XXs`**.

---

## 🛠️ 8. Solución de Problemas Comunes (Troubleshooting)

| Problema | Causa Probable | Solución |
| :--- | :--- | :--- |
| **Error 401 Unauthorized en n8n** | El `BACKEND_API_KEY` en n8n no coincide con `backend/.env`. | Verifica que `BACKEND_API_KEY` tenga el mismo valor en `backend/.env` y en los headers de n8n. |
| **Error de conexión a `http://backend:8000` desde n8n** | n8n no está en la misma red Docker que el backend. | Asegúrate de levantar ambos servicios con `docker compose up` para que compartan la red `lumina_network`. En local fuera de Docker, usa `http://localhost:8000`. |
| **Error `Rate Limit Exceeded` (429)** | Se superó el límite de peticiones por minuto configurado en `RATE_LIMIT_PER_MINUTE`. | Espera 60 segundos o incrementa el valor en `backend/.env` (ej. `60/minute`). |
| **ChromaDB retorna resultados irrelevantes** | El índice vectorial necesita sincronizarse tras subir nuevos documentos. | Ingresa al panel de administración (`/admin/login`) -> pestaña **Documentos RAG** y vuelve a subir el archivo `.md` para forzar la reindexación automática. |

---

¡Tu entorno de **Academia Lumina AI** y **n8n** está completamente listo y operativo para producción!
