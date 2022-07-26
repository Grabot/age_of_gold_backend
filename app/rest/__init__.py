from flask import Blueprint

app_api = Blueprint('api', __name__)


from app.rest import hexagon_rest
from app.rest import map_rest
from app import q


# @app_api.route("/")
# def home():
#     return render_template('index.html')


def background_task():
    print("background")
    return True


@app_api.route('/task')
def add_task():
    job = q.enqueue(background_task)
    q_len = len(q)
    return f"Task {job.id} added to queue at {job.enqueued_at}. {q_len} tasks in the queue"

