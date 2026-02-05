FROM python:3.14.1-slim

WORKDIR /

RUN apt-get update && \
    apt-get install -y --no-install-recommends git gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

ENV PYTHONPATH=${PYTHONPATH}:/src

COPY /age_of_gold_worker/age_of_gold_worker /age_of_gold_worker/age_of_gold_worker
COPY /age_of_gold_worker/__init__.py /age_of_gold_worker/__init__.py
COPY /age_of_gold_worker/pyproject.toml /age_of_gold_worker/pyproject.toml

COPY pyproject.toml /pyproject.toml
COPY README.md /README.md

RUN uv pip install --system --no-cache-dir -e .

COPY boot.sh /boot.sh
COPY main.py /main.py
COPY migrations/ /migrations/
COPY alembic.ini /alembic.ini
COPY src/ /src/

RUN useradd -r -s /bin/false -m celery && \
    mkdir -p /home/celery/ && \
    chown -R celery:celery /home/celery
