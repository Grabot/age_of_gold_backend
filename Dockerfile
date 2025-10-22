FROM python:3.14-slim

WORKDIR /
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN apt-get update &&\
    apt install -y git gcc libpq-dev &&\
    pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir poetry && \
    pip3 install --no-cache-dir pre-commit && \
    poetry config virtualenvs.create false

COPY pyproject.toml /pyproject.toml
COPY boot.sh /boot.sh
COPY main.py /main.py
COPY main_cron.py /main_cron.py
COPY migrations/ /migrations/
COPY alembic.ini /alembic.ini

RUN useradd -r -s /bin/false -m celery && \
    mkdir -p /home/celery/ && \
    chown -R celery:celery /home/celery

RUN poetry install --no-root --only main

COPY src/ /src/
RUN mkdir -p static/uploads
RUN chown -R celery:celery /src
