import time

import requests
from celery import Celery
from config.config import settings

app = Celery(
    "tasks",
    broker=settings.REDIS_URI,
    backend=f"db+{settings.DB_URL}",
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
