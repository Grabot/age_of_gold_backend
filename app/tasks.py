import os
import time

import requests
from celery import Celery

POSTGRES_URL = os.environ["POSTGRES_URL"]
POSTGRES_PORT = os.environ["POSTGRES_PORT"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]

REDIS_URL = os.environ["REDIS_URL"]
REDIS_PORT = os.environ["REDIS_PORT"]

PASSWORD_AGE_OF_GOLD = os.environ["PASSWORD_AGE_OF_GOLD"]

DB_URL = "postgresql+asyncpg://{user}:{pw}@{url}:{port}/{db}".format(
    user=POSTGRES_USER,
    pw=POSTGRES_PASSWORD,
    url=POSTGRES_URL,
    port=POSTGRES_PORT,
    db=POSTGRES_DB,
)

REDIS_URI = "redis://{url}:{port}".format(url=REDIS_URL, port=REDIS_PORT)


app = Celery(
    "tasks",
    broker=REDIS_URI,
    backend=f"db+{DB_URL}",
)


@app.task
def task_add(count: int, delay: int):
    url = "https://randomuser.me/api"
    response = requests.get(f"{url}?results={count}").json()["results"]
    time.sleep(delay)
    result = []
    for item in response:
        print(f"item test {item}")
    return {"success": result}
