FROM nginx:alpine
# Копируем наш конфигурационный файл (например, prod.conf) в нужное место
COPY ./prod.conf /etc/nginx/nginx.conf
EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]
