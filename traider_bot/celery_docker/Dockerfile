FROM python:3.12

WORKDIR /app
COPY bot-python/traider_bot .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

#RUN adduser --disabled-password service-user
#USER service-user