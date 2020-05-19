FROM python:3.8-slim

ENV APP_HOME=/home/app/web

RUN mkdir -p $APP_HOME

WORKDIR $APP_HOME

RUN apt-get update && \
    apt-get -y install netcat && \
    apt-get clean

COPY . .

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["./entrypoint.sh"]
