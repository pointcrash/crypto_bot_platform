FROM python:3.9-slim

WORKDIR /app
COPY /bot-python/traider_bot/tg_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY /bot-python/traider_bot/tg_bot/start_app.py .

CMD ["python", "start_app.py"]
