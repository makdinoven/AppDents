# Stage 1: сборка приложения
FROM node:22-alpine AS builder
WORKDIR /app
# Копируем package.json и package-lock.json (или yarn.lock)
COPY package*.json ./
RUN npm install --legacy-peer-deps
# Копируем исходный код
COPY . .
# Собираем приложение (статические файлы попадают в папку dist)
RUN npm run build

# Stage 2: отдача статики через Nginx
FROM nginx:alpine

# Копируем собранные файлы в стандартную папку nginx для статики
COPY --from=builder /app/dist /usr/share/nginx/html

# Экспонируем порт (по умолчанию nginx слушает на 80)
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
