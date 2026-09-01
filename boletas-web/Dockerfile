# Sitio público de consulta de boletas: build con Node, servido por nginx.
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# El RUT del emisor se fija al construir: cada despliegue publica un emisor.
ARG VITE_ISSUER_RUT
ENV VITE_ISSUER_RUT=$VITE_ISSUER_RUT
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
