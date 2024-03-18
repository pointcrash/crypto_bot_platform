FROM python:3.11

COPY /bot-python/traider_bot/requirements.txt /bot-python/traider_bot/app/requirements.txt
WORKDIR /bot-python/traider_bot/app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY ./bot-python/traider_bot /bot-python/traider_bot/app

ENV DJANGO_SETTINGS_MODULE=traider_bot.settings
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1

# Копируем скрипт запуска в контейнер
COPY /bot-python/traider_bot/run.sh /bot-python/traider_bot/app/run.sh

# Делаем скрипт исполняемым
RUN chmod +x /bot-python/traider_bot/app/run.sh

# Устанавливаем скрипт запуска как ENTRYPOINT
ENTRYPOINT ["/bot-python/traider_bot/app/run.sh"]

