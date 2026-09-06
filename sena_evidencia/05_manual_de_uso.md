# 05. Manual de Instalación, Configuración y Uso: Academia Lumina AI

Este documento proporciona la guía técnica paso a paso para desplegar el sistema en entornos locales y en la nube, la especificación de variables de entorno y las instrucciones operativas para cada uno de los roles del sistema.

---

## 1. Requisitos del Sistema

### 1.1 Entorno de Ejecución Recomendado (Docker)
- **Docker Engine**: versión 24.0.0 o superior.
- **Docker Compose**: versión 2.20.0 o superior.
- **Memoria RAM**: 4 GB mínimo recomendado (para ejecutar Backend, Frontend y n8n simultáneamente).
- **Almacenamiento**: 5 GB de espacio libre en disco.

### 1.2 Entorno de Ejecución Nativo (Sin Docker)
- **Python**: versión 3.12.x (con soporte `venv` y `pip`).
- **Node.js**: versión 20.x o superior (con `npm` 10+).
- **Navegador Web**: Google Chrome, Mozilla Firefox, Microsoft Edge o Safari (versiones actualizadas).

---

## 2. Variables de Entorno del Sistema

### 2.1 Backend (`backend/.env`)

| Variable | Requerida | Propósito / Valor Ejemplo |
| :--- | :---: | :--- |
| `GROQ_API_KEY` | **SÍ** | Clave de API de Groq Cloud para la inferencia de lenguaje (`gsk_...`). |
| `GEMINI_API_KEY` | **SÍ** | Clave de Google AI Studio para generación de embeddings vectoriales. |
| `BACKEND_API_KEY`| **SÍ** | Secreto compartido para validar solicitudes del frontend y n8n (`lumina_secret_key_2026`). |
| `JWT_SECRET_KEY` | **SÍ** | Clave criptográfica para la firma de tokens de sesión JWT de asesores. |
| `ADMIN_USERNAME` | **SÍ** | Usuario predeterminado del administrador para entorno local (`admin`). |
| `ADMIN_PASSWORD` | **SÍ** | Contraseña predeterminada del administrador para entorno local (`admin123`). |
| `DATABASE_URL` | NO | URL de conexión SQL. Si se omite, usa `sqlite:///./lumina.db`. En producción: `postgresql://user:pass@host:5432/lumina`. |
| `FRONTEND_URL` | NO | URL pública del frontend para enlaces de retorno en alertas (`https://mi-dominio.com`). |
| `ALLOWED_ORIGINS`| **SÍ** | Orígenes CORS permitidos separados por coma (`http://localhost:3000,http://127.0.0.1:3000`). |
| `RATE_LIMIT_PER_MINUTE` | NO | Límite de peticiones por minuto por cliente IP (`10/minute`). |
| `ADVISOR_NAME` | NO | Nombre institucional del asesor visible en notificaciones (`Asesor de Admisiones Lumina`). |
| `WHATSAPP_NUMBER`| NO | Teléfono de WhatsApp para el botón de contacto directo (`+57 300 000 0000`). |
| `WHATSAPP_URL` | NO | Enlace directo para apertura de WhatsApp (`https://wa.me/573000000000`). |
| `ESCALATION_EMAIL`| NO | Correo electrónico institucional para recepción de alertas de supervisión. |
| `SMTP_HOST` / `PORT` | NO | Servidor SMTP para envío de correos salientes (`smtp.gmail.com` / `587`). |
| `SMTP_USER` / `PASSWORD`| NO | Credenciales de autenticación del servidor de correo. |

### 2.2 Frontend (`frontend/.env`)

| Variable | Requerida | Propósito / Valor Ejemplo |
| :--- | :---: | :--- |
| `VITE_BACKEND_URL` | **SÍ** | URL base del servidor FastAPI (`http://localhost:8000` en local o URL en la nube). |
| `VITE_BACKEND_API_KEY` | **SÍ** | Clave de API idéntica a `BACKEND_API_KEY` del backend. |

---

## 3. Guía de Instalación y Ejecución

### 3.1 Puesta en Marcha Rápida con Docker Compose (Recomendado)

1. **Clonar el repositorio**:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd PruebaDesempe-oAI
   ```

2. **Configurar variables de entorno**:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   # Editar backend/.env con su GROQ_API_KEY y GEMINI_API_KEY reales
   ```

3. **Compilar y levantar los servicios**:
   ```bash
   docker compose up -d --build
   ```

4. **Verificar estado de los contenedores**:
   ```bash
   docker compose ps
   ```
   Deben aparecer 3 contenedores activos y saludables:
   - `lumina_backend` (Puerto 8000)
   - `lumina_frontend` (Puerto 3000)
   - `lumina_n8n` (Puerto 5678)

5. **Ejecutar la suite de pruebas automatizadas**:
   ```bash
   docker exec lumina_backend pytest -v
   ```

---

### 3.2 Despliegue en la Nube (Plataforma Render)

El proyecto incluye el manifiesto declarativo `render.yaml` y la guía `RENDER_DEPLOYMENT.md`. Para desplegar:

1. **Crear Base de Datos PostgreSQL en Render**:
   - Tipo: PostgreSQL Database (Free Tier).
   - Copiar la cadena de conexión interna (`Internal Database URL`).

2. **Crear Web Service del Backend (FastAPI)**:
   - Entorno: **Docker** (apunta a la subcarpeta `backend/Dockerfile` o raíz con context).
   - Configurar variables de entorno en Render:
     - `DATABASE_URL`: Pegar la URL de PostgreSQL.
     - `GROQ_API_KEY`: Clave de Groq.
     - `GEMINI_API_KEY`: Clave de Gemini.
     - `BACKEND_API_KEY`: Clave de seguridad del backend.
     - `JWT_SECRET_KEY`: Secreto JWT para tokens.
     - `ALLOWED_ORIGINS`: La URL pública de tu frontend en Render.
     - `FRONTEND_URL`: La URL pública de tu frontend en Render.

3. **Crear Static Site o Web Service del Frontend (React)**:
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`
   - Variables de entorno:
     - `VITE_BACKEND_URL`: URL pública asignada a tu backend en Render (ej. `https://lumina-backend.onrender.com`).
     - `VITE_BACKEND_API_KEY`: La misma `BACKEND_API_KEY`.

---

## 4. Manual de Usuario por Roles

### 4.1 Perspectiva del Estudiante / Visitante Web
1. **Acceso al Portal**: Ingresa a `http://localhost:3000`. Visualiza la landing page con la propuesta de valor y oferta académica de Academia Lumina.
2. **Apertura del Chat**: En la esquina inferior derecha, pulsa el botón flotante dorado con el icono de mensaje. Se despliega la ventana conversacional.
3. **Consulta de Información (RAG)**: Escribe preguntas en español o inglés, tales como:
   - *"¿Cuáles son los precios del curso de inglés intensivo?"*
   - *"¿Qué horarios tienen disponibles los fines de semana?"*
   - *"What certifications do you offer?"*
   El sistema responde en menos de un segundo, indicando las fuentes oficiales utilizadas.
4. **Solicitud de Asesor Humano**: Si deseas hablar con una persona, escribe: *"Quiero hablar con un asesor de admisiones"*. El chat pasará a estado de espera de atención humana.
5. **Chat en Vivo**: Tan pronto como un asesor tome el caso, aparecerá el indicador *"El asesor [Nombre] se ha conectado"*. La conversación continúa en tiempo real a través de WebSockets.

---

### 4.2 Perspectiva del Asesor de Admisiones
1. **Acceso al Panel**: Dirígete a `http://localhost:3000/admin` o haz clic en "Acceso Asesores".
2. **Autenticación**: Ingresa tu usuario y contraseña (por defecto: `admin` / `admin123`).
3. **Bandeja de Entrada (Inbox)**:
   - En la pestaña **"Bandeja de Entrada"**, revisa la lista de conversaciones divididas en:
     - **Pendientes**: Casos escalados que esperan atención.
     - **En Atención**: Casos asignados a ti o a otros asesores.
     - **Resueltos**: Historial de casos cerrados.
4. **Toma de Caso (Claim)**: Haz clic en una conversación pendiente. Revisa la tarjeta de resumen ejecutivo con los datos del prospecto y pulsa **`[🙋‍♂️ Tomar Caso]`**. La conversación pasará a estar bajo tu responsabilidad exclusiva.
5. **Atención por WebSocket**: Escribe mensajes en el campo de texto inferior. Tus respuestas se sincronizan instantáneamente con la pantalla del estudiante.
6. **Resolución del Caso**: Una vez brindada la orientación requerida, pulsa el botón verde **`[✅ Marcar Resuelto]`**. El canal se cerrará ordenadamente.
7. **Atención Alternativa vía Telegram**: Si estás fuera de tu equipo, recibirás la alerta en el canal de Telegram con los botones interactivos `[🙋‍♂️ Tomar Caso]`, `[✅ Caso Resuelto]` y `[💬 Abrir WhatsApp]`.

---

### 4.3 Perspectiva del Administrador / Supervisor
1. **Supervisión de Métricas Operacionales**:
   - En el panel administrativo, pulsa la pestaña **"Métricas y Operaciones"**.
   - Evalúa el cumplimiento de SLA, la tasa de resolución autónoma del bot IA, el índice CSAT y la gráfica de volumen de tickets.
   - Observa la tarjeta de **Ahorro de Costos y Tokens**, que cuantifica el dinero ahorrado en la API de Groq gracias al motor de caché semántico en memoria.
2. **Actualización de la Base de Conocimiento (RAG)**:
   - Haz clic en la pestaña **"Documentos"** o **"Base de Conocimiento"**.
   - Arrastra nuevos documentos oficiales (`.pdf`, `.docx`, `.md` o `.txt`) correspondientes a nuevas circulares, listas de precios o convenios.
   - Pulsa **"Procesar e Indexar"**. El sistema segmentará el documento e indexará los nuevos vectores en ChromaDB de inmediato, sin necesidad de reiniciar el servidor ni interrumpir las operaciones.
