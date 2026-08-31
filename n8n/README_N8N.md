# Guía de Importación y Configuración del Workflow n8n - Academia Lumina

Este directorio contiene el flujo automatizado oficial de **n8n** (`workflow.json`) diseñado como un **Router Puro** para integrar la recepción de mensajes, el procesamiento con el backend RAG en FastAPI y el envío de notificaciones por correo electrónico en caso de escalamiento a asesor humano.

---

## 1. Arquitectura del Flujo n8n

El flujo automatizado se compone de 5 nodos conectados secuencialmente:

1. **Webhook - Recepción de Consulta**:
   - Escucha peticiones `POST` en `/webhook/chat`.
   - Recibe la pregunta enviada desde el formulario o widget de chat web.
2. **HTTP Request - Router FastAPI RAG**:
   - Reenvía el mensaje al backend FastAPI (`POST http://localhost:8000/api/v1/chat`).
   - Envía automáticamente la cabecera de autenticación `X-API-Key: lumina_secret_key_2026`.
3. **¿Requiere Escalamiento? (Nodo IF)**:
   - Evalúa el parámetro booleano `is_escalated`.
   - Si `is_escalated == true`, activa la rama de escalamiento.
4. **Notificación Correo Interno Admisiones**:
   - En la rama de escalamiento, envía un correo automático a `admisiones@academialumina.co` con el resumen de la consulta y el enlace a WhatsApp.
5. **Respuesta al Cliente (Respond to Webhook)**:
   - Retorna la respuesta generada al usuario final con código HTTP 200.

---

## 2. Instrucciones para Importar en n8n

1. Abre tu panel de control de n8n (local o en la nube).
2. Haz clic en **Workflows** -> **Import from File**.
3. Selecciona el archivo `n8n/workflow.json`.
4. Configura las credenciales SMTP para el nodo de envío de correo en `Notificación Correo Interno Admisiones`.
5. Activa el workflow haciendo clic en el switch **Active**.

---

## 3. Ejemplo de Prueba con cURL

Puedes probar el Webhook de n8n ejecutando el siguiente comando en tu terminal:

```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Tienen programas de intercambio cultural a Canadá?",
    "session_id": "sesion_demo_01"
  }'
```

**Respuesta Esperada**:
```json
{
  "response": "No cuento con información sobre programas de intercambio cultural en nuestros documentos oficiales. Para brindarte una mejor atención personalizada, por favor ponte en contacto directo con uno de nuestros asesores por WhatsApp: https://wa.me/573247836387.",
  "is_escalated": true,
  "whatsapp_link": "https://wa.me/573247836387",
  "session_id": "sesion_demo_01"
}
```
