FROM python:3.10.11-slim-buster

RUN mkdir -p /home/app

RUN addgroup --system app && adduser --system --group app

ENV HOME=/home/app
ENV APP_HOME=/home/app/api
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && apt-get install ffmpeg libsm6 libxext6  -y

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . $APP_HOME

RUN chown -R app:app $APP_HOME

USER app

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]