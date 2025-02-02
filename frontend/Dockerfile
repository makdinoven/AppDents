# # Этап 1: Сборка
# FROM node:20-alpine AS build
# WORKDIR /frontend
# COPY package*.json ./
# RUN npm install pnpm
# RUN npm install --legacy-peer-deps
# COPY . .
# # RUN npm run build  # создает папку dist

# # Этап 2: Подготовка минимального образа с nginx
# FROM nginx:stable-alpine
# RUN rm /etc/nginx/conf.d/default.conf

# COPY default.conf /etc/nginx/conf.d/default.conf
# # Копируем финальную сборку (dist) внутрь Nginx
# # COPY --from=build /frontend/dist /usr/share/nginx/html

# EXPOSE 3002
# # CMD ["nginx", "-g", "daemon off;"]
# CMD ["pnpm", "run", "dev"]

FROM node:22-alpine

# Установка рабочей директории
WORKDIR /frontend

# Копирование package.json и package-lock.json
COPY /package*.json ./

# Установка зависимостей
RUN npm install pnpm
RUN npm install

# Копирование исходного кода
COPY . .

# Установка переменных окружения для React
ENV CHOKIDAR_USEPOLLING=true

# Команда запуска разработческого сервера
CMD ["pnpm", "run", "dev"]