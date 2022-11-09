import os
from dotenv import load_dotenv

# loads the environment variable file
load_dotenv()


class Config(object):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # Configuration
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_DISCOVERY_URL = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )

    GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
    GITHUB_ACCESS = "https://github.com/login/oauth/access_token"
    GITHUB_USER = "https://api.github.com/user"
    GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", None)
    GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", None)

    REDDIT_AUTHORIZE = "https://www.reddit.com/api/v1/authorize"
    REDDIT_ACCESS = "https://www.reddit.com/api/v1/access_token"
    # REDDIT_USER = "https://api.github.com/user"
    REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", None)
    REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", None)
    REDDIT_REDIRECT = "https://ageof.gold/login/reddit/callback"
    DEBUG = True


class DevelopmentConfig(Config):
    POSTGRES_URL = os.environ["POSTGRES_URL"]
    POSTGRES_PORT = os.environ["POSTGRES_PORT"]
    POSTGRES_USER = os.environ["POSTGRES_USER"]
    POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
    POSTGRES_DB = os.environ["POSTGRES_DB"]

    REDIS_URL = os.environ["REDIS_URL"]
    REDIS_PORT = os.environ["REDIS_PORT"]

    PASSWORD_AGE_OF_GOLD = os.environ["PASSWORD_AGE_OF_GOLD"]

    DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}:{port}/{db}'.format(
        user=POSTGRES_USER, pw=POSTGRES_PASSWORD, url=POSTGRES_URL, port=POSTGRES_PORT, db=POSTGRES_DB)

    REDIS_URL = "redis://{url}:{port}".format(url=REDIS_URL, port=REDIS_PORT)

    SQLALCHEMY_DATABASE_URI = DB_URL
