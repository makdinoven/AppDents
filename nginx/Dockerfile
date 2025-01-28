FROM nginx:alpine

# Копируем конфигурационный файл Nginx
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]