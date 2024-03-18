FROM python:3.11

COPY /ByBit_bot/traider_bot/requirements.txt /ByBit_bot/traider_bot/app/requirements.txt
WORKDIR /ByBit_bot/traider_bot/app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY ./ByBit_bot/traider_bot /ByBit_bot/traider_bot/app

ENV DJANGO_SETTINGS_MODULE=traider_bot.settings
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1

# Копируем скрипт запуска в контейнер
COPY /ByBit_bot/traider_bot/run.sh /ByBit_bot/traider_bot/app/run.sh

# Делаем скрипт исполняемым
RUN chmod +x /ByBit_bot/traider_bot/app/run.sh

# Устанавливаем скрипт запуска как ENTRYPOINT
ENTRYPOINT ["/ByBit_bot/traider_bot/app/run.sh"]

