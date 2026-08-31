# Etapa 1: Construcción de la aplicación React con Vite
FROM node:20-alpine AS build

WORKDIR /app

# Copiar paquetes e instalar dependencias
COPY package*.json ./
RUN npm ci

# Copiar código fuente y construir estáticos
COPY . .
RUN npm run build

# Etapa 2: Servidor Web Nginx ligero para servir los estáticos
FROM nginx:alpine

# Copiar la configuración optimizada de Nginx o usar la por defecto
COPY --from=build /app/dist /usr/share/nginx/html

# Exponer el puerto 80 dentro del contenedor (mapeado a 3000 en compose)
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
