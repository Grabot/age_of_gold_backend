FROM python:3.10-slim-bullseye

RUN apt-get update

COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

COPY boot.sh ./
RUN chmod u+x boot.sh

COPY age_of_gold.py ./
COPY migrations ./migrations/
COPY app ./app/
COPY .env ./

EXPOSE 5000
ENTRYPOINT ["/bin/sh", "boot.sh"]