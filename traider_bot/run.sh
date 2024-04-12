#!/bin/bash

# Выполняем миграции
pip install -r requirements.txt

python manage.py migrate
python manage.py collectstatic --no-input

# Отправляем менеджеру сигнал о запуске
python ./traider_bot/start_ws_manager.py

# Запускаем сервер gunicorn
gunicorn traider_bot.wsgi:application --bind 0.0.0.0:8000 --workers 1 --timeout 0 --pid gunicorn.pid
