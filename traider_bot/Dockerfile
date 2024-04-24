
FROM python:3.11

#COPY /bot-python/traider_bot/requirements.txt /app/requirements.txt
WORKDIR /app

# Создаем и активируем виртуальное окружение
RUN pip install virtualenv
RUN virtualenv venv
SHELL ["/bin/bash", "-c"]
RUN source venv/bin/activate


RUN pip install --upgrade pip
#RUN pip install -r requirements.txt
RUN pip install gunicorn

#COPY /bot-python/traider_bot /app

#ENV DJANGO_SETTINGS_MODULE=traider_bot.settings
#ENV PYTHONDONTWRITEBYTECODE 1
#ENV PYTHONUNBUFFERED=1

# Делаем скрипт исполняемым
RUN chmod +x /app/run.sh

# Устанавливаем скрипт запуска как ENTRYPOINT
ENTRYPOINT ["/app/run.sh"]





