FROM python:3.11

WORKDIR /app
COPY bot-python/traider_bot .
# Создаем и активируем виртуальное окружение
RUN pip install virtualenv
RUN virtualenv venv
SHELL ["/bin/bash", "-c"]
RUN source venv/bin/activate


RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

# Делаем скрипт исполняемым
RUN chmod +x /app/run.sh

# Устанавливаем скрипт запуска как ENTRYPOINT
ENTRYPOINT ["/app/run.sh"]
