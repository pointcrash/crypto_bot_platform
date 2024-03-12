FROM python:3.11

COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app

ENV DJANGO_SETTINGS_MODULE=traider_bot.settings
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1

# Копируем скрипт запуска в контейнер
COPY run.sh /app/run.sh

# Делаем скрипт исполняемым
RUN chmod +x /app/run.sh

# Устанавливаем скрипт запуска как ENTRYPOINT
ENTRYPOINT ["/app/run.sh"]

#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
