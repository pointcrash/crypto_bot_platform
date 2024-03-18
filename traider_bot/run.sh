#!/bin/bash

# Выполняем миграции
python manage.py migrate

# Отправляем менеджеру сигнал о запуске
python ./traider_bot/start_ws_manager.py

# Запускаем сервер Django
#python manage.py runserver 0.0.0.0:8000

# Запускаем сервер gunicorn
gunicorn traider_bot.wsgi:application --bind 0.0.0.0:8000