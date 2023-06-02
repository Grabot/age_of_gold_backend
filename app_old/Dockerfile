FROM python:3.10-slim-bullseye

RUN apt-get update

WORKDIR /app_old

COPY requirements.txt /app_old/requirements.txt
RUN pip install -r requirements.txt

COPY boot.sh ./
RUN chmod u+x boot.sh

COPY age_of_gold.py ./
COPY migrations ./migrations/
COPY . ./app_old/
COPY .env ./
RUN mkdir -p static/uploads

EXPOSE 5000
ENTRYPOINT ["/bin/sh", "boot.sh"]
