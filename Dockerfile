FROM python:3.10.6-slim-bullseye

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

COPY app /app/.
COPY pyproject.toml /app/pyproject.toml

RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

RUN mkdir -p static/uploads

EXPOSE 5000
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
#CMD ["python3", "main.py"]
