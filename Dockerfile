FROM python:3.14.1-slim

WORKDIR /

RUN apt-get update && \
    apt-get install -y --no-install-recommends git gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

ENV PYTHONPATH=${PYTHONPATH}:/src

COPY /age_of_gold_worker/age_of_gold_worker /age_of_gold_worker/age_of_gold_worker

COPY pyproject.toml /pyproject.toml
COPY README.md /README.md

RUN uv pip install --system --no-cache-dir -e .

COPY boot.sh /boot.sh
COPY main.py /main.py
COPY migrations/ /migrations/
COPY alembic.ini /alembic.ini
COPY src/ /src/

RUN mkdir -p /src/static/uploads
