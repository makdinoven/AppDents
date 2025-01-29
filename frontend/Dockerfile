# Этап 1: Сборка
FROM node:20-alpine AS build
WORKDIR /frontend
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build  # создает папку dist

# Этап 2: Подготовка минимального образа с nginx
FROM nginx:stable-alpine
RUN rm /etc/nginx/conf.d/default.conf

COPY default.conf /etc/nginx/conf.d/default.conf
# Копируем финальную сборку (dist) внутрь Nginx
COPY --from=build /frontend/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
