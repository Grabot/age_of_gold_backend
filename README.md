# Age of GOLD

This is the backend of the Age of GOLD project. Here we will store the hexagonal map information.

## Pre-requisites

### variables

to get this project up and running you first need to assign a bunch of variables.
An important one is the `JWT_PEM` variable. This is the private key used to sign the JWT tokens. You can generate one by looking at the `generate_pem.py` script. Here a new random pem is generated and then encoded in base64. This base64 string is then used as the `JWT_PEM` variable in the .env, don't expose this string anywhere. For this script you need the `PRIVATE_KEY_PASSPHRASE` variable. Make sure that this is the same as what you define in the .env and again don't share it anywhere.


#### postgres

For the database connection you need `POSTGRES_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` and `POSTGRES_PORT` (but this will probably be 5432). The database is a postgresql container that is started alongside the api via the `docker-compose.yaml` file. It will use these variables to create the connection string and connect. The `POSTGRES_URL` can be the name of the container in the yaml file. So default values that should work are
POSTGRES_URL="age_of_db"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="password"
POSTGRES_DB="database"
POSTGRES_PORT=5432
Here the name of the database will be `database`.

#### Redis

Furthermore the project will use a REDIS database which requires a `REDIS_URL` and `REDIS_PORT` (which will probably be 6379). Similarly the connection can be done by setting the `REDIS_URL` to the container name, so default values that should work are
REDIS_URL="redis"
REDIS_PORT=6379

#### Mail

For sending the mails, like when you forgot your password, we are using Brevo. You need to create an account and get an API key (not SMTP key). and fill that API-key in the `MAIL_API_KEY` variable.
Make sure you have authorized the domain you are using.


#### Oauth2

##### Google

For signin in or up with using your google account you need to create a project in the google cloud console. Then you need to create a OAuth2 client ID for a browser app. You need to fill in the `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` variables with the values from the newly created entry. Make sure you add the correct redirect URLs in `GOOGLE_REDIRECT_URL`.

##### Reddit

Similarly you want to add a oauth2 web client in the reddit app prefs settings. You need to fill in the `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` variables with the values from the newly created entry. Make sure you add the correct redirect URLs in `REDDIT_REDIRECT_URL`.

##### Github

Again here you want to add a oauth2 web client in the github developer settings. You need to fill in the `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` variables. Make sure you add the correct redirect URLs in `GITHUB_REDIRECT_URL`.

##### Apple

For Apple you want to ensure that you have an app id that matches your mobile application. Ensure this by uploading a placeholder app. Make sure this has the sign in with apple capability enabled.After this you can create a service id. With this service id you can setup the oauth logging. Set the `APPLE_CLIENT_ID` to the value of this service id.
Other information you can set are the `APPLE_TEAM_ID` which is the team id of your apple developer account.
Next create a key with "sign in with apple" functionality. Set the `APPLE_KEY_ID` with the value of this key. You should get an option to "download" the key. This will be your `APPLE_AUTH_KEY`. Download this and set it in the `.env` file (replace newlines with \n).
You define the redirect url in the service id. Make sure this matches the `APPLE_REDIRECT_URL` variable.


## Run in dev

Some services need to be running and configured; you can start them with podman-compose.

Build the AoG image:

    uv run podman build -t aog .

    or

    uv run podman-compose build

Run the image you just built:

    uv run podman run -it aog

    or

    uv run podman-compose up


## Upload to docker hub


uv run podman build -t age_of_gold:<version> .
uv run podman image tag age_of_gold:<version> <docker_hub_username>/age_of_gold:<version>
uv run podman push <docker_hub_username>/bro_cast:<version>


### Things to consider when starting a new project
