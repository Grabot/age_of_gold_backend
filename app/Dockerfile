FROM python:3.10-slim-bullseye

COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
COPY . /app/.
COPY .env ./
RUN mkdir -p static/uploads

EXPOSE 5000
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
#CMD ["python3", "main.py"]
ENTRYPOINT ["/bin/sh", "boot.sh"]
