# Guía de Importación y Configuración de Workflows n8n - Academia Lumina

Este directorio contiene los flujos de automatización oficiales de **n8n** diseñados para operar de forma integrada con el backend RAG en FastAPI de **Academia Lumina AI**.

---

## 1. Inventario de Workflows

### 📁 1. Router de Consultas y Escalamiento (`workflow.json`)
* **Tipo de Trigger**: Webhook (`POST /webhook/chat`)
* **Propósito**: Actúa como punto de entrada (o pasarela) para consultas de clientes. Reenvía el mensaje al backend (`POST http://backend:8000/api/v1/chat`), evalúa si la respuesta requirió escalamiento a humano (`is_escalated == true`), envía una alerta por email a admisiones si es el caso, y responde al webhook con la respuesta RAG estructurada.

### 📁 2. Monitor de SLA de Atención Humana (`workflow_sla.json`)
* **Tipo de Trigger**: Schedule / Cron (Cada 5 minutos)
* **Propósito**: Consulta al endpoint administrativo `GET http://backend:8000/api/v1/admin/conversations/sla/breached?threshold_minutes=10` con cabecera `X-API-Key`. Si hay conversaciones en cola de espera pendientes por más de 10 minutos sin ser tomadas por un asesor, dispara un correo de alerta de alta prioridad a los supervisores con el conteo y las sesiones afectadas.

### 📁 3. Reporte Diario Ejecutivo de Métricas (`workflow_reportes.json`)
* **Tipo de Trigger**: Schedule / Cron (Diario a las 8:00 AM)
* **Propósito**: Consume el endpoint `GET http://backend:8000/api/v1/metrics` con cabecera `X-API-Key`. Compila un informe ejecutivo con el total de consultas, tasa de aciertos de caché semántico, tasa de escalamiento a humanos, latencia promedio y total de tokens consumidos/costo estimado en USD, despachándolo por correo al equipo directivo.

---

## 2. Variables de Entorno en n8n

Para el correcto funcionamiento en Docker o producción, asegúrate de configurar las siguientes variables de entorno en el contenedor o instancia de n8n:

| Variable | Descripción | Valor por Defecto / Ejemplo |
|---|---|---|
| `BACKEND_API_KEY` | API Key secreta para autenticar peticiones contra el backend | `lumina_secret_key_2026` |
| `SMTP_SENDER_EMAIL` | Remitente del servidor de correo | `admissions@academialumina.edu.co` |
| `ESCALATION_EMAIL` | Destinatario de alertas y reportes | `supervisors@academialumina.edu.co` |

---

## 3. Instrucciones de Importación en n8n

1. Accede a tu instancia de n8n (ej. `http://localhost:5678` en local o tu URL en la nube).
2. Ve a la sección **Workflows**.
3. Haz clic en el menú contextual (tres puntos) o botón **Import from File**.
4. Selecciona cualquiera de los tres archivos (`workflow.json`, `workflow_sla.json` o `workflow_reportes.json`).
5. Configura las credenciales de tu servicio de correo (SMTP, Gmail, SendGrid u otro) en los nodos de envío de email correspondientes.
6. Activa el workflow con el interruptor **Active** / **Publish**.

---

## 4. Pruebas Rápidas con cURL

### Prueba de Webhook de Chat:
```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuáles son los requisitos de admisión para el diplomado en IA?",
    "session_id": "test_n8n_01"
  }'
```

### Prueba de Endpoint SLA en Backend:
```bash
curl -X GET "http://localhost:8000/api/v1/admin/conversations/sla/breached?threshold_minutes=10" \
  -H "X-API-Key: lumina_secret_key_2026"
```

### Prueba de Endpoint de Métricas en Backend:
```bash
curl -X GET "http://localhost:8000/api/v1/metrics" \
  -H "X-API-Key: lumina_secret_key_2026"
```
