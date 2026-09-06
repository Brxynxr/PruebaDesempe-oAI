# 06. Reporte de Evidencias Visuales y Capturas de Pantalla: Academia Lumina AI

Este documento certifica el estado de las capturas de pantalla de la aplicación tomadas en tiempo real directamente sobre los contenedores Docker en ejecución (`lumina_frontend`, `lumina_backend`, `lumina_n8n`).

---

## 1. Inventario de Capturas Generadas (En `sena_evidencia/screenshots/`)

Todas las pantallas principales del sistema fueron capturadas de forma automatizada y se encuentran almacenadas en formato PNG de alta resolución dentro del directorio `sena_evidencia/screenshots/`:

| Archivo de Captura | Vista de la Aplicación | Descripción Detallada de la Evidencia | Estado |
| :--- | :--- | :--- | :---: |
| **`01_landing.png`** | Portal Web Público | Página principal de Academia Lumina (`http://localhost:3000`), mostrando el Hero institucional, propuesta de valor, oferta de programas y el botón flotante de atención. | **Capturada (100%)** |
| **`02_chat_respuesta_bot.png`** | Chatbot RAG en Acción | Widget de chat desplegado con una consulta académica real en español ("¿Cuáles son los horarios y modalidades...?"), mostrando la respuesta contextualizada de Groq LPU citando las fuentes oficiales. | **Capturada (100%)** |
| **`03_login_admin.png`** | Portal de Asesores | Formulario de autenticación segura (`http://localhost:3000/admin`) con campos de usuario, contraseña enmascarada y credenciales protegidas con Bcrypt/JWT. | **Capturada (100%)** |
| **`04_bandeja_agentes.png`** | Inbox de Casos en Vivo | Consola del Asesor mostrando el listado de conversaciones activas, tarjetas de resumen ejecutivo de prospectos (leads) y botones de acción rápida. | **Capturada (100%)** |
| **`05_dashboard_metricas.png`** | Tablero de Operaciones y SLA | Panel de control con analítica en tiempo real: tasa de resolución autónoma de IA, cumplimiento de tiempos de respuesta (SLA), CSAT y ahorro en tokens/costos ($ USD). | **Capturada (100%)** |
| **`06_base_conocimiento.png`** | Ingesta de Documentos | Módulo administrativo de carga de archivos curriculares multiformato (`.pdf`, `.docx`, `.md`, `.txt`) con división en fragmentos (chunking) y reindexación automática en ChromaDB. | **Capturada (100%)** |

---

## 2. Estado de Pendientes en la Aplicación Web

- **Total de capturas requeridas de la plataforma web**: 6
- **Total de capturas obtenidas exitosamente**: 6
- **Capturas pendientes en el entorno web**: **0 (Ninguna pendiente)**

---

## 3. Captura Complementaria Opcional (Canal Telegram Móvil)

Todas las vistas de la aplicación web y panel administrativo están cubiertas al 100%. De manera complementaria, si para el informe final del SENA se desea ilustrar la interacción remota desde un dispositivo móvil con Telegram, el usuario puede capturar manualmente:

- **Nombre sugerido**: `07_telegram_alerta_botones.png`
- **Contenido**: Pantalla de la aplicación Telegram en el teléfono o escritorio donde el bot de Lumina envía la alerta de nuevo caso con los botones interactivos inline:
  - `[🙋‍♂️ Tomar Caso]`
  - `[✅ Caso Resuelto]`
  - `[💬 Abrir WhatsApp]`
  - `[📊 Panel Admin]`

*Nota: Esta captura de Telegram es netamente ilustrativa del canal externo móvil; la totalidad de la arquitectura del software, base de datos y paneles web ya se encuentra documentada y capturada.*
