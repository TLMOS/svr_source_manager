FROM python:3.10-slim

WORKDIR /home

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && apt-get install ffmpeg libsm6 libxext6  -y

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ./services/api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./common ./common
COPY ./services/api .

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--worker-class", \
     "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
