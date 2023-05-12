FROM python:3.10.11-slim-buster

WORKDIR /home

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && apt-get install ffmpeg libsm6 libxext6  -y

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--log-level", "warning", \ 
     "--host", "0.0.0.0", "--port", "8000"]