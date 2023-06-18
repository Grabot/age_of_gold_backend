FROM python:3.10.6-slim-bullseye

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

COPY app /app/.
COPY pyproject.toml /app/pyproject.toml

# static dependencies
RUN apt-get update &&\
    apt install -y git &&\
    pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir poetry && \
    pip3 install --no-cache-dir pre-commit && \
    poetry config virtualenvs.create false

RUN poetry install --no-dev

RUN mkdir -p static/uploads

RUN git init &&\
    pre-commit run --all-files

EXPOSE 5000

#ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
ENTRYPOINT ["python3", "main.py"]
