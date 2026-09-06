# ⚙️ Módulo de Automatización n8n - Academia Lumina AI

Este directorio alberga los **4 flujos de automatización declarativos** en formato JSON que conectan el backend de Academia Lumina con Telegram y gestionan las alertas de supervisión y reportería.

---

## 📋 Catálogo de Workflows

| Archivo | Tipo de Activador | Propósito | Integraciones |
| :--- | :---: | :--- | :--- |
| **`workflow.json`** | Webhook (`POST /webhook/chat`) | **Escalamiento en Vivo a Asesores**: Recibe alertas de estudiantes que solicitan asesor humano. Envía tarjeta a Telegram con botones interactivos: `[🙋‍♂️ Tomar Caso]`, `[✅ Caso Resuelto]`, `[💬 Abrir WhatsApp]` y `[📊 Panel Admin]`. | Backend FastAPI ➔ n8n ➔ Telegram Bot API |
| **`workflow_leads.json`** | Webhook (`POST /webhook/leads`) | **Captura Comercial de Prospectos**: Notifica al equipo de admisiones de nuevos leads con nombre, teléfono y programa de interés. | Backend FastAPI ➔ n8n ➔ Telegram |
| **`workflow_sla.json`** | Cron programado (Cada 1 min) | **Supervisor de SLA**: Consulta periódicamente los tickets en estado `pendiente`. Si superan los 15 minutos sin ser reclamados, emite una alerta de incumplimiento de SLA con botón de resolución forzada. | n8n Cron ➔ Backend API ➔ Telegram |
| **`workflow_reportes.json`**| Cron diario (8:00 AM) | **Consolidado Ejecutivo Diario**: Extrae métricas del endpoint `/api/v1/metrics` (resolución autónoma, CSAT, tokens ahorrados) y despacha el reporte matutino al canal de supervisión. | n8n Cron ➔ Backend API ➔ Telegram |

---

## 🚀 Puesta en Marcha

1. El contenedor de n8n se levanta automáticamente con Docker Compose:
   ```bash
   docker compose up -d lumina_n8n
   ```
2. Accede a la consola de n8n en: [http://localhost:5678](http://localhost:5678)
3. Crea tu cuenta local de administrador en n8n.
4. Para cada flujo:
   - Ve a **Workflows** ➔ **Import from File...**
   - Selecciona el archivo `.json` correspondiente (`workflow.json`, `workflow_leads.json`, etc.).
   - Configura las credenciales de tu **Telegram Bot Token** y el **Chat ID** del grupo de admisiones.
   - Pulsa **Activate** en la esquina superior derecha.
