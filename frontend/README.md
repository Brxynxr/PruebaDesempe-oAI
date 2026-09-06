# 🌐 Frontend Web - Academia Lumina AI

Cliente web interactivo desarrollado con **React 18**, **Vite 5** y **Tailwind CSS v4**. Ofrece una experiencia de usuario fluida tanto para estudiantes y prospectos en el portal público, como para los asesores comerciales en la consola administrativa.

---

## 🌟 Características de la Interfaz

1. **Landing Page Institucional (`LandingPage.jsx`)**:
   - Presentación de la propuesta de valor de Academia Lumina (programas de inglés, francés, alemán, italiano y español).
   - Tipografía refinada (*Playfair Display* / *Inter*), gradientes de fondo cálidos y paleta institucional *Egyptian Sand & Gold*.
   - Botón flotante accesible de atención en línea.
2. **Widget Conversacional Inteligente (`FloatingChat.jsx`)**:
   - Soporte híbrido: inicia con peticiones HTTP (`/chat`) y activa **WebSockets bidireccionales** (`/ws/chat/{session_id}`) al requerir atención humana.
   - Detección de idioma automática con respuestas contextualizadas y citas a fuentes oficiales.
   - Transiciones visuales dinámicas de estado (`bot` ➔ `pendiente` ➔ `en_atencion` ➔ `resuelto`).
3. **Portal del Asesor y Consola en Vivo (`AdminDashboard.jsx`)**:
   - **Bandeja de Chats**: Visualización en tiempo real de conversaciones activas segmentadas por estado (*Todas*, *Pendientes*, *En curso*, *Resueltas*).
   - **Tarjeta de Resumen de Lead**: Desglose inmediato del nombre del prospecto, teléfono de contacto y programa de interés.
   - **Toma Atómica de Casos (`[Tomar caso]`)**: Bloquea la conversación para que ningún otro asesor interfiera.
   - **Mensajería en Vivo**: Chat bidireccional mediante WebSocket (`/ws/agent`) con respuestas rápidas sugeridas.
   - **Métricas y Operaciones**: Dashboard con gráficos analíticos de resolución por IA, tiempos de SLA, distribución por idiomas y costos/tokens ahorrados.
   - **Base RAG (Gestión Documental)**: Módulo interactivo con drag-and-drop para subir archivos `.pdf`, `.docx`, `.md` o `.txt` con reindexación vectorial instantánea.
4. **Autenticación Administrativa Segura (`AdminLogin.jsx`)**:
   - Formulario con persistencia segura de token JWT en `localStorage`.
   - Protección contra navegación no autenticada hacia `/admin`.

---

## 📂 Estructura de Directorios del Frontend

```text
frontend/
├── public/                    # Archivos públicos y estáticos (Favicon SVG)
├── src/
│   ├── assets/                # Imágenes institucionales optimizadas (Campus, aulas, avatares)
│   ├── components/
│   │   ├── AdminDashboard.jsx # Consola integral de asesores (Chats, Métricas, Base RAG)
│   │   ├── AdminLogin.jsx     # Formulario de inicio de sesión con JWT
│   │   ├── FloatingChat.jsx   # Widget conversacional flotante (HTTP + WebSocket)
│   │   └── LandingPage.jsx    # Portal de bienvenida institucional
│   ├── lib/
│   │   └── utils.js           # Helpers de clases CSS (clsx + tailwind-merge)
│   ├── services/
│   │   └── api.js             # Cliente API REST y gestión de tokens/WebSockets
│   ├── styles.css             # Estilos globales y directivas de Tailwind CSS v4
│   ├── App.jsx                # Enrutador principal SPA (/ y /admin)
│   └── main.jsx               # Montaje en el árbol DOM de React
├── Dockerfile                 # Construcción multi-stage (Node builder + Nginx Alpine)
├── nginx.conf                 # Servidor web Nginx configurado para rutas SPA
├── package.json               # Dependencias de npm
└── vite.config.js             # Configuración del empaquetador Vite
```

---

## 🔑 Variables de Entorno (`frontend/.env`)

```bash
cp .env.example .env
```

| Variable | Descripción | Valor por Defecto |
| :--- | :--- | :--- |
| `VITE_BACKEND_URL` | URL base del servidor backend FastAPI | `http://localhost:8000` |
| `VITE_BACKEND_API_KEY` | Clave API secreta compartida con el backend | `lumina_secret_key_2026` |

---

## 🚀 Ejecución y Desarrollo

### Con Docker Compose (Recomendado)
```bash
docker compose up -d lumina_frontend
```
Disponible en: [http://localhost:3000](http://localhost:3000)

### En Entorno Node.js Nativo
```bash
cd frontend
npm install
npm run dev
```

### Compilación para Producción
```bash
npm run build
```
Genera la carpeta optimizada `dist/` en ~2.8 segundos.
