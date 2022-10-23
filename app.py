from gevent import monkey

monkey.patch_all()

from app import create_app
from app import socks


app = create_app()


if __name__ == "__main__":
    app.run(ssl_context='adhoc')
    # app.run(host="0.0.0.0", debug=True)
    # socks.run(app, host="0.0.0.0", debug=True)

