# Guía de Workflows Oficiales n8n — Academia Lumina AI

Este directorio contiene los flujos de automatización oficiales de **n8n** diseñados para operar de forma 100% integrada con el backend FastAPI RAG y las alertas en tiempo real a **Telegram** de **Academia Lumina AI**.

---

## 1. Inventario de Workflows

### 📁 1. Router de Consultas y Escalamiento (`workflow.json`)
* **Trigger**: Webhook (`POST /webhook/chat`)
* **Acción**: 
  1. Recibe la consulta del usuario vía Webhook.
  2. Consulta al backend RAG (`POST http://backend:8000/api/v1/chat`).
  3. Evalúa si la respuesta requiere escalamiento a humano (`is_escalated == true`).
  4. Si requiere escalamiento, envía una alerta prioritaria en **HTML a Telegram** con el detalle del caso, enlace directo a WhatsApp y enlace al panel administrativo.
  5. Retorna al llamador la respuesta sintetizada y las fuentes documentales.

### 📁 2. Notificación Inmediata de Leads a Telegram (`workflow_leads.json`)
* **Trigger**: Webhook (`POST /webhook/leads`)
* **Acción**:
  1. Recibe el registro inmediato de nuevo prospecto desde el backend.
  2. Envía alerta enriquecida a Telegram con nombre, WhatsApp, programa y enlace directo al panel.

### 📁 3. Monitor de SLA de Atención Humana (`workflow_sla.json`)
* **Trigger**: Schedule / Cron (Cada 1 minuto `* * * * *`)
* **Acción**: 
  1. Consulta `GET http://backend:8000/api/v1/admin/conversations/sla/breached?threshold_minutes=1` con cabecera `X-API-Key: lumina_dev_api_key_2026`.
  2. Evalúa en código JS los casos en espera y extrae las sesiones y tiempos de retraso.
  3. Si hay casos esperando atención (`count > 0`), despacha una alerta de SLA crítica a Telegram con el listado de casos prioritarios y enlace al panel de asesores.

### 📁 3. Reporte Diario Ejecutivo de Métricas (`workflow_reportes.json`)
* **Trigger**: Schedule / Cron (Diario a las 8:00 AM `0 8 * * *`)
* **Acción**: 
  1. Consume el endpoint `GET http://backend:8000/api/v1/metrics`.
  2. Compila un informe ejecutivo formateado con métricas de resolución IA, acierto de caché, tasa de escalamiento, cumplimiento de SLA, latencia promedio, tokens y costos.
  3. Despacha el informe ejecutivo a Telegram.

---

## 2. Configuración de Telegram

Los flujos están preconfigurados con las credenciales oficiales del Bot de Notificaciones:
* **Bot Token**: `8856257947:AAF3buxaPS5fSmBQWPY0IG6GCjwPEdR_oyU`
* **Chat ID**: `7761516818`
* **Parse Mode**: `HTML`

---

## 3. Instrucciones de Importación en la Interfaz Web de n8n

1. Accede a tu interfaz de n8n en el navegador: [http://localhost:5678](http://localhost:5678).
2. Ve al menú **Workflows** en la barra lateral izquierda.
3. Haz clic en el botón de opciones (tres puntos `...`) en la esquina superior derecha y selecciona **Import from File**.
4. Selecciona cualquiera de los archivos JSON (`workflow.json`, `workflow_sla.json` o `workflow_reportes.json`).
5. El workflow se cargará automáticamente con todos sus nodos, rutas, expresiones `JSON.stringify` y conectores listos.
6. Activa el interruptor **Active** (o botón **Publish**) en la esquina superior derecha.

---

## 4. Pruebas Rápidas con cURL

### Prueba 1: Webhook de Consulta RAG (Sin Escalamiento)
```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuáles son los programas de idiomas y sus niveles?",
    "session_id": "test_n8n_01"
  }'
```

### Prueba 2: Webhook con Escalamiento y Alerta a Telegram
```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quiero hablar con un asesor humano urgente sobre los pagos",
    "session_id": "test_n8n_escalation"
  }'
```

### Prueba 3: Consulta Manual de Casos SLA en Backend
```bash
curl -X GET "http://localhost:8000/api/v1/admin/conversations/sla/breached?threshold_minutes=1" \
  -H "X-API-Key: lumina_dev_api_key_2026"
```

### Prueba 4: Consulta Manual de Métricas en Backend
```bash
curl -X GET "http://localhost:8000/api/v1/metrics" \
  -H "X-API-Key: lumina_dev_api_key_2026"
```
