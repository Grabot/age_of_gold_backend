FROM python:3.10.6-slim-bullseye

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

# install static dependencies
RUN apt-get update &&\
    apt install -y git &&\
    pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir poetry && \
    pip3 install --no-cache-dir pre-commit && \
    poetry config virtualenvs.create false

# add dependency file
COPY pyproject.toml /app/pyproject.toml

# install project dependencies
RUN poetry install --no-dev

# add other project files
COPY app /app/.
COPY .pre-commit-config.yaml .flake8 /app/
RUN mkdir -p static/uploads

# test & lint
RUN git init &&\
    git checkout -b ci &&\
    pre-commit run --all-files
