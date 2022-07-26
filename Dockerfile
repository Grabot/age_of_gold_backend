FROM python:3.9.10

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

COPY boot.sh ./
COPY worker.py ./
RUN chmod u+x boot.sh

EXPOSE 5000
EXPOSE 6379
ENTRYPOINT ["/bin/sh", "boot.sh"]