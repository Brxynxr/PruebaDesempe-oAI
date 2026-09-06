# 🚀 Guía de Despliegue Mínimo Funcional en Render — Academia Lumina AI

Esta guía detalla el procedimiento exacto paso a paso para desplegar **Academia Lumina AI** en la nube de **Render** de manera 100% funcional, segura y persistente.

---

## 🔒 1. Paso Crítico Previo: Rotación de Secretos

Antes de realizar el push o desplegar en Render:

1. **Telegram Bot Token:**
   - Abre Telegram y habla con [@BotFather](https://t.me/botfather).
   - Ejecuta `/revoke` y selecciona el bot de Academia Lumina para invalidar el token anterior.
   - Genera un nuevo token y cópialo de forma segura (este token solo se colocará en las variables de entorno de Render).

2. **Credenciales de Administración y Seguridad:**
   - Define una nueva contraseña segura para `ADMIN_PASSWORD`.
   - Genera una cadena aleatoria para `JWT_SECRET_KEY` (ej. `openssl rand -hex 32`).
   - Genera una clave segura para `BACKEND_API_KEY` (ej. `openssl rand -hex 24`).

---

## 🗄️ 2. Paso 1: Crear la Base de Datos PostgreSQL en Render

1. En el Dashboard de Render, haz clic en **New +** → **PostgreSQL**.
2. Configura los parámetros:
   - **Name:** `lumina-postgres`
   - **Database:** `lumina_db`
   - **User:** `lumina_user`
   - **Region:** Selecciona la más cercana (ej. Oregon / Ohio / Frankfurt).
   - **Plan:** Free o Starter.
3. Haz clic en **Create Database**.
4. Una vez creada, copia el **Internal Database URL** (ej. `postgresql://lumina_user:...@dpg-xxx:5432/lumina_db`).

---

## ⚙️ 3. Paso 2: Crear el Web Service del Backend en Render

1. Haz clic en **New +** → **Web Service**.
2. Conecta tu repositorio de GitHub / GitLab.
3. Configura las opciones principales:
   - **Name:** `academia-lumina-backend`
   - **Region:** La misma que tu base de datos PostgreSQL.
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/api/v1/health`
   - **Instance Type / Plan:** **Starter (Always-On)**  
     > ⚠️ **IMPORTANTE:** El plan gratuito se suspende por inactividad, lo cual detiene el hilo de Telegram y corta las conexiones WebSockets. El plan **Always-On** garantiza atención en vivo ininterrumpida.

4. En la sección **Environment Variables**, agrega:

| Variable | Valor / Descripción |
| :--- | :--- |
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | Tu Internal Database URL de PostgreSQL de Render |
| `GROQ_API_KEY` | Tu clave de Groq API (`gsk_...`) |
| `GEMINI_API_KEY` | Tu clave de Google Gemini API (`AIzaSy...`) |
| `BACKEND_API_KEY` | Tu clave interna secreta generada |
| `JWT_SECRET_KEY` | Tu clave aleatoria para tokens JWT |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | Tu contraseña administrativa segura |
| `ALLOWED_ORIGINS` | `https://academia-lumina-frontend.onrender.com` *(URL de tu frontend)* |
| `FRONTEND_URL` | `https://academia-lumina-frontend.onrender.com` *(URL base del frontend)* |
| `TELEGRAM_BOT_TOKEN` | Tu nuevo token de bot revocado |
| `TELEGRAM_CHAT_ID` | El ID del grupo/chat de asesores en Telegram |
| `RATE_LIMIT_PER_MINUTE` | `60/minute` |

5. Haz clic en **Create Web Service**.

---

## 🌐 4. Paso 3: Crear el Static Site del Frontend en Render

1. Haz clic en **New +** → **Static Site**.
2. Conecta el mismo repositorio.
3. Configura los parámetros:
   - **Name:** `academia-lumina-frontend`
   - **Branch:** `main`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Publish Directory:** `dist`

4. En la sección **Environment Variables**:

| Variable | Valor |
| :--- | :--- |
| `VITE_BACKEND_URL` | `https://academia-lumina-backend.onrender.com` *(La URL pública de tu backend en Render)* |
| `VITE_BACKEND_API_KEY` | El mismo valor que configuraste en `BACKEND_API_KEY` en el backend |

5. Configura **Redirects/Rewrites** (para SPA en React Router):
   - **Source:** `/*`
   - **Destination:** `/index.html`
   - **Action:** `Rewrite`

6. Haz clic en **Create Static Site**.

---

## ✅ 5. Checklist de Verificación End-to-End

Una vez finalizado el despliegue, valida los siguientes puntos en la URL pública:

1. [ ] **Landing Page y Chat IA:** Abre `https://academia-lumina-frontend.onrender.com`, abre el widget de chat centrado y consulta información de cursos (inglés, precios, horarios).
2. [ ] **Escalamiento y Lead:** Haz una consulta fuera de catálogo (ej. "¿Tienen parqueadero propio?"). Verifica que el bot sugiera el asesor y al hacer clic en "Sí, conectar con un asesor", solicita Nombre y WhatsApp.
3. [ ] **Alerta en Telegram:** Comprueba que en el grupo de Telegram llega la alerta con el ID de sesión visible y los botones de acción ("Tomar Caso", "Caso Resuelto").
4. [ ] **Respuesta desde Telegram:** Responde desde Telegram usando Reply o `/responder [id_sesion] tu mensaje` y verifica que el texto llega en tiempo real al chat del estudiante en el navegador sin recargar.
5. [ ] **Panel Administrativo:** Ingresa a `https://academia-lumina-frontend.onrender.com/admin` con tus credenciales de admin y comprueba la bandeja en tiempo real conectada por WebSocket.
6. [ ] **Persistencia en PostgreSQL:** Ejecuta un "Manual Deploy" en Render del backend y comprueba que las conversaciones y usuarios creados se conservan íntegros.

---

## 📌 6. Alcance y Backlog Posterior

- **n8n:** No bloquea el despliegue del chat ni del panel de asesores. Puede alojarse posteriormente en n8n Cloud o en un servicio separado.
- **Sentry, Redis, CI y WCAG:** Quedan registrados en el backlog para fases posteriores de escalabilidad empresarial.
