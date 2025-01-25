# frontend/Dockerfile

# Этап сборки
FROM node:22-alpine as build

# Установка рабочей директории
WORKDIR /app

# Копирование package.json и package-lock.json
COPY package.json package-lock.json ./

# Установка зависимостей
RUN npm install

# Копирование исходного кода
COPY ./src ./src
COPY ./public ./public

# Сборка приложения
RUN npm run build

# Этап продакшен
FROM nginx:alpine

# Копирование собранного приложения из предыдущего этапа
COPY --from=build /app/build /usr/share/nginx/html

# Копирование кастомного конфигурационного файла Nginx
COPY ../nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Открытие порта 80
EXPOSE 80

# Команда запуска Nginx
CMD ["nginx", "-g", "daemon off;"]
