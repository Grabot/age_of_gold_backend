from gevent import monkey

monkey.patch_all()

from app_old import create_app, socks

app = create_app()


if __name__ == "__main__":
    # app_old.run(ssl_context='adhoc')
    # app_old.run(host="0.0.0.0", debug=True)
    socks.run(app, host="0.0.0.0", debug=True)
