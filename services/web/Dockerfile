FROM python:3.10.11-slim-buster

RUN mkdir -p /home/app

RUN addgroup --system app && adduser --system --group app

ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

RUN apt-get update \
    && apt-get -y install gcc

RUN pip install uwsgi

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . $APP_HOME

RUN chown -R app:app $APP_HOME

USER app

CMD ["uwsgi", "--ini", "uwsgi.ini", "--http", "0.0.0.0:5000"]