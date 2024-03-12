#!/bin/bash

# Ожидаем доступности базы данных PostgreSQL
/wait-for-it.sh db:5432 -t 30

# Выполняем миграции
python manage.py migrate

# Запускаем сервер Django
python manage.py runserver 0.0.0.0:8000
