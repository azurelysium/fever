ARG BASE_IMAGE=python:3.9-slim
FROM $BASE_IMAGE

WORKDIR /app
RUN apt-get update && apt-get install -y make dumb-init

COPY ./requirements.txt /app/requirements.txt
RUN pip install -U pip
RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["make", "run"]
