FROM python:3.11

WORKDIR /app

COPY bot-python/traider_bot .
RUN pip install -r requirements.txt

CMD ["python", "manage.py", "qcluster"]
