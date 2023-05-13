FROM python:3.10-alpine

RUN addgroup -S app && adduser -S app -G app

WORKDIR /home

RUN apk add python3-dev build-base linux-headers pcre-dev  && \
    apk --no-cache add musl-dev linux-headers g++

RUN pip install uwsgi

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . $APP_HOME

RUN chown -R app:app /home

USER app

EXPOSE 5000

CMD ["uwsgi", "--ini", "uwsgi.ini", "--http", "0.0.0.0:5000"]