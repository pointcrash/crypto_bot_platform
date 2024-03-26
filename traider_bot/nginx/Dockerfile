FROM nginx:latest

RUN apt-get update && apt-get install -y ssl-cert

RUN make-ssl-cert generate-default-snakeoil

# Путь к файлу указан относительно расположения docker-compose файла
COPY /bot-python/traider_bot/nginx/nginx.conf /etc/nginx/

EXPOSE 80
EXPOSE 443
