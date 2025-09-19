# Stage 1: сборка приложения
FROM node:22-alpine AS builder
WORKDIR /app
# Копируем package.json и package-lock.json (или yarn.lock)
COPY package*.json ./
RUN npm install --legacy-peer-deps
# Копируем исходный код
COPY . .

# Кэш для vite/esbuild, детальный вывод на время отладки
# (убери DEBUG после диагностики)
ENV DEBUG="vite:*,rollup:*"
RUN --mount=type=cache,target=/root/.cache/vite \
    --mount=type=cache,target=/root/.cache/esbuild \
    npm run build:prod

############################
# Stage 2: Static via Nginx
############################
# Stage 2: отдача статики через Nginx
FROM nginx:alpine
# Копируем собранные файлы из stage builder в стандартную папку nginx для статики
COPY --from=builder /app/dist /usr/share/nginx/html
# Копируем кастомную конфигурацию Nginx для SPA fallback
# Если frontend.conf лежит в корне каталога фронтенда, то:
COPY frontend.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
