FROM python:3.10.11-slim-buster

RUN addgroup --system app && adduser --system --group app

WORKDIR /home

RUN apt-get update \
    && apt-get -y install gcc

RUN pip install uwsgi

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . $APP_HOME

RUN chown -R app:app /home

USER app

CMD ["uwsgi", "--ini", "uwsgi.ini", "--http", "0.0.0.0:5000"]