#!/bin/bash

# Выполняем миграции
python manage.py migrate
python manage.py collectstatic --no-input

# Отправляем менеджеру сигнал о запуске
python ./traider_bot/start_ws_manager.py

# Запускаем сервер gunicorn
gunicorn traider_bot.wsgi:application --bind 0.0.0.0:8000