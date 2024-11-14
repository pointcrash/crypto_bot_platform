FROM python:3.12

WORKDIR /app
COPY bot-python/traider_bot .
# Создаем и активируем виртуальное окружение
#RUN pip install virtualenv
#RUN virtualenv venv
#SHELL ["/bin/bash", "-c"]
#RUN source venv/bin/activate


RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

# Делаем скрипт исполняемым
RUN chmod +x /app/run.sh

#RUN adduser --disabled-password service-user
#USER service-user

# Устанавливаем скрипт запуска как ENTRYPOINT
ENTRYPOINT ["/app/run.sh"]
