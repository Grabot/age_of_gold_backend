# Age of Gold

This is the backend of the Age of Gold project.

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

create a proton account with (at least) mail plus
https://account.proton.me/u/2/mail/imap-smtp
Add a domain and follow the instructions.
Go to settings -> IMAP/SMTP
Generate a new token with a address of your choosing.
For the given SMTP username you will get a token and the SMTP server details
Fill all these details in the following variables: `SMTP_PASSWORD`, `SMTP_ACCOUNT`, `SMTP_HOST`, `SMTP_PORT` Fill in your own value for `SMTP_USER`.
You will now send emails via the proton mail account you have entered.

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

    podman build -t age_of_gold:<version> .
    or
    podman-compose build

Run the image you just built:

    podman run -it age_of_gold:<version>
    or
    podman-compose up


### Build the worker

There is a celery worker which is used to create the avatars and to send the emails without stopping the endpoint calls.
To build the container of the worker you can run

    podman build -f age_of_gold_worker/Dockerfile_worker -t age_of_gold_worker:<worker_version> .


### Build the cron worker

There is a simple cron job which is used to remove expired tokens from the database. It only uses the files required to remove the tokens instead of the entire project.
To build the container of the cron worker you can run

    podman build -f age_of_gold_cron/Dockerfile_cron -t age_of_gold_cron:<worker_version> .

## Upload to docker hub

first login with the cli to your account

    podman login

Then build and upload the container

    podman build -t <project_name>:<version> .
    podman image tag <project_name>:<version> <docker_hub_username>/<project_name>:<version>
    podman push <docker_hub_username>/<project_name>:<version>


## Deploy on a server (Hetzner)

### Get a new dedicated server instance

Get an instance where you can ssh into. We want to add a user specific for the project and add a kubernetes cluster holding the containers. We wil add a nginx configuration to the cluster to serve the frontend after the dns configuration.

After you bought a server you want to setup, first run installimage. Choose what you want, I choose ubuntu

After that's done do a reboot and you should have the server running, but probably not all the disks correctly partionened.
Check with `parted -l`

If one or more disks are not correctly recognized or used you have to partioned them, which you can do like this for every disk

    gdisk /dev/sdx
        - 0
        - w
    gdisk /dev/sdx
        - n
        - w
    mkfs.ext4 /dev/sdx1

Next make some place to actually mount these disks, like `mnt/sdx`. Edit the `/etc/fstab` file to include these such that they are mounted on started (if it doesn't exist you have to create it)

    # <file system>    <mount point>  <type>  <options>  <dump>  <pass>
    /dev/sdx1          /mnt/sdx       ext4    defaults    0       2

Use `df -h` to see if the mount worked and the drives are operational.

To add this new server as a node to the kubernetes cluster follow this:
https://community.hetzner.com/tutorials/managed-kubernetes-with-hetzner-dedicated-servers-with-cloudfleet

    hostnamectl set-hostname my-dedicated-server-<random_number>
    sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

Add the self managed node in cloudfleet

    Site region: Hetzner
    Site zone: <server location from robot>
    node hostname: <server ip>
    ssh user name: root
    ssh key path <full path to private key>

Execute the command that is then given
    cloudfleet clusters add-self-managed-node <some id given by cloudfleet> --host <server ip>  --ssh-username root --ssh-key <full path to private key>--region <site region> --zone <site zone>

The node should now be added.


### Get the server ready


    apt-get update -y
    apt-get upgrade -y

Install restic for the backup

    apt-get install restic

Create and add a new ssh key and add the ssh key of the node to the storage box

    ssh-keygen -t ed25519 -f /root/.ssh/hetzner_storage_box_key -N ""
    cat /root/.ssh/hetzner_storage_box_key.pub | ssh -p23 <u_storage_box>@<u_storage_box>..your-storagebox.de install-ssh-key

Initialize the storage box for the node (if not yet done)

    restic -r sftp://<u_storage_box>@<u_storage_box>..your-storagebox.de:23/backups/postgresql/ init

Set a storage-box password and put this as the `RESTIC_PASSWORD` in the restic yaml. Set the `RESTIC_REPOSITORY` to `sftp://<u_storage_box>@<u_storage_box>.your-storagebox.de:23/backups/postgresql` which is your hetzner storage box connection.

Create a temp `known_hosts` file to finish the `restic-secret.yaml`. Do this with

    ssh-keyscan -p 23 u517638.your-storagebox.de > known_hosts

Now you can cat the private key you just made and the known hosts and paste them in the `restic-secret.yaml` in `SSH_PRIVATE_KEY` and `KNOWN_HOSTS` in base64 encoding respectively.

    cat known_hosts or ssh private key | base64 -w 0

You can access the storage box via sftp like this.

    sftp -oPort=23 -i <path_to_key> <u_storage_box>@<u_storage_box>.your-storagebox.de
    or just use ssh
    ssh -i <path_to_key> -p 23 <u_storage_box>@<u_storage_box>.your-storagebox.de

### Setup a new project on your kubernetes cluster (on a single node)

Execute the yamls in order, but for each yaml make sure you first do some pre work

1.  - *Namespace:*
    - Replace <namespace> tag in all the yamls with something that fits your project
	- Apply the namespace yaml

2.	- Fastapi secret
    - Pick values for the `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB`.
	- encode the values in base64: `echo -n '<value>' | base64`
	- apply the secrets yaml

3.	- Redis database
    - Replace the <kubernetes-node-name> tag with the kubernetes node where you are installing this project
	- apply the redis yaml

4.	- Postgresql database
    - Replace the <kubernetes-node-name> tag with the kubernetes node where you are installing this project
	- Replace the <data-folder> tag with the path where you want the data to be placed
		- Make sure this path exists on the node
	- apply the postgresql yaml
    - You can access the psql with `kubectl exec -it <postgres-pod-name> -n <namespace> -- psql -U <username> -d <database-name>`

5.	- FastAPI backend
    - Replace the <kubernetes-node-name> tag with the kubernetes node where you are installing this project
	- Replace <docker_hub_username>/<project_repo>:<version> with the url that points to your docker hub project container
	- Fill in all the env variables that you will be using (and possibly some that are not listed)
	- Pick an port to expose it to outside the cluster
		- Make sure this does not interfer with other exposed ports on the cluster.
	- Apply the FastAPI yaml
	- Validate that the FastAPI started up and that it connected to the database
		- get all pods with `kubectl get pods -n <namespace>`
		- look in the logs of the FastAPI container with `kubectl logs -n <namespace> <container_name>
			- It should show the alembic script and application startup logs

6.	- FastAPI worker
    - Replace the <kubernetes-node-name> tag with the kubernetes node where you are installing this project
	- Replace <docker_hub_username>/<project_repo>:<version> with the url that points to your docker hub project container
	- Fill in all the env variables that you will be using (and possibly some that are not listed)
	- Apply the worker yaml.

7.	- FastAPI cronjob
    - Replace the <kubernetes-node-name> tag with the kubernetes node where you are installing this project
	- Replace <docker_hub_username>/<project_repo>:<version> with the url that points to your docker hub project container
	- Fill in all the env variables that you will be using (and possibly some that are not listed)
	- Apply the cron worker yaml.

8.	- Restic-secret (backup)
    - Fill in the values for `RESTIC_REPOSITORY` and `RESTIC_PASSWORD` from your hetzner storage-box details.
	- Create a new ssh (If not already done) and add it on the storage box
		- ssh-keygen -t ed25519 -f /root/.ssh/hetzner_storage_box_key -N ""
		- cat /root/.ssh/hetzner_storage_box_key.pub | ssh -p23 <hetzner-storage-box-user>@<hetzner-storage-box-address-link> install-ssh-key
	- Fill in the ssh private key in the `SSH_PRIVATE_KEY` field as a base64 encoded string
	- make a known_hosts file
		- ssh-keyscan -p 23 <hetzner-storage-box-address-link> > known_hosts
		- copy the content of this file as a base64 encoded string in the `KNOWN_HOSTS` field.
	- Apply the restic backup yaml

9.	- Restic backup cronjobs
    - Replace the <kubernetes-node-name> tag with the kubernetes node where you are installing this project
	- Replace the <data-folder> with the folder that you also gave when creating the persisten volume (step 4)
	- Apply the restic backup cronjob yamls

10.	- Restic check service (optional)
	- When doing a backup, apply the restic service yaml.
        - It will run at the crontime, but you can trigger a manual job like this: `kubectl create job --from=cronjob/postgres-backup postgres-backup-$(date +%Y%m%d%H%M%S) -n <namespace>`
		- To see all the backups execute:
			- kubectl exec -it restic-check -n <namespace> -- sh -c 'restic snapshots'
		- To remove a specific snapshot
			- kubectl exec -it restic-check -n <namespace> -- sh -c 'restic forget <snapshot_id>'
		- Check only the latest snapshots for all the folders
			- kubectl exec -it restic-check -n <namespace> -- sh -c 'restic snapshots --latest 1'
		- Go through all the backed up files
			- First restore it on the storage-box (and clear the folder your are restoring to)
                - kubectl exec -it restic-check -n <namespace> -- sh -c 'rm -rf /tmp/restore/*'
				- kubectl exec -it restic-check -n <namespace> -- sh -c 'restic restore <snapshot_id> --target /tmp/restore'
			- Copy it on your own computer
				- kubectl cp <namespace>/restic-check:/tmp/restore <target on own computer> -c restic --retries 10
			- You can now do what you want with the files, even restore a previous state on the server
                - `scp -r /path/to/local/folder root@server_ip:/path/to/destination/folder`
                - tip: First zip the files and then copy them over to the server
                    - scp <file_path> root@server_ip:<destionation>
                    - from the node: unzip -d <zip_file> .

11. - Frontend
    - Replace the <kubernetes-node-name> tag with the kubernetes node where you are installing this project
    - Replace <docker_hub_username>/<frontend_project_repo>:<version> with the url that points to your docker hub project container
    - Fill in the port the frontend uses and pick an port to expose it to outside the cluster
		- Make sure this does not interfer with other exposed ports on the cluster.
    - Fill in any environment variable the porject uses.
    - If applicable you can now apply the frontend.
<!--

## Setup kubernetes cluster (using cloudfleet)

https://community.hetzner.com/tutorials/managed-kubernetes-with-hetzner-dedicated-servers-with-cloudfleet

## Set nginx configuration (outdated?)


First we want to ensure that the dns of the domain is configured to point to the ip of the server.
Do this in the DNS configuration of the domain by setting an A record to the ip of the server.
The url will be the `<url_dns_configuration>`

Second we want to create a directory for our website with the url the same as what we configured in the DNS.

    sudo mkdir -p /var/www/<url_dns_configuration>/html
    sudo chown -R $USER:$USER /var/www/<url_dns_configuration>/html
    sudo chmod -R 755 /var/www/<url_dns_configuration>

Create a placeholder `index.html` to test the configuration.

    sudo vi /var/www/<url_dns_configuration>/html/index.html
    Doesn't matter what you put in the index.html.

Now create the nginx configuration file in `/etc/nginx/sites-available/<url_dns_configuration>`

It will look something like this
```
server {
    root /var/www/<url_dns_configuration>/html;
    index index.php index.html index.htm;

    server_name <url_dns_configuration> www.<url_dns_configuration>;

	client_max_body_size 1G; # Set this to the maximum file size you want to allow

    location / {
        try_files $uri $uri/ /index.html;
    }

    # The backend only exposes the api endpoints and the socket connection
    # The frontend is the index.html which will be shown when going to the root path.
    location /api/ {
        include proxy_params;
        proxy_pass <fastapi-service_cluster-ip>:<fastapi-service_port>;
    }

    location /socket.io {
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_hide_header 'Access-Control-Allow-Origin';
        proxy_pass <fastapi-service_cluster-ip>:<fastapi-service_port>/socket.io;
    }
}
```

Next create a symbolic link to the sites-enabled folder

    sudo ln -s /etc/nginx/sites-available/<url_dns_configuration> /etc/nginx/sites-enabled/

Ensure the NGINX configura  tion is error-free.

    sudo nginx -t

After setting up the server blocks, restart NGINX to apply the changes.

    sudo systemctl restart nginx

Now you should see the index html page when going to the url
You still have to go to the unsecured `http` but it should show what you put in the `index.html`

## Set up secure SSL connection using certbot

First make sure it is installed

    apt install python3-certbot-nginx

Get the SSL Security Certificate

    certbot run --nginx -d example.com,www.example.com

### Setup Automatic SSL Renewal

For this purpose, by adding the extension script to /etc/cron.d, we can perform the renewal process automatically.

After receiving the SSL, the /etc/cron.d/certbot file is created to renew the SSL security certificate with the following contents.

```
/etc/cron.d/certbot: crontab entries for the certbot package

Upstream recommends attempting renewal twice a day

Eventually, this will be an opportunity to validate certificates
haven't been revoked, etc.  Renewal will only occur if expiration
is within 30 days.

Important Note!  This cronjob will NOT be executed if you are
running systemd as your init system.  If you are running systemd,
the cronjob.timer function takes precedence over this cronjob.  For
more details, see the systemd.timer manpage, or use systemctl show
certbot.timer.

SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

0 */12 * * * root test -x /usr/bin/certbot -a \! -d /run/systemd/system && perl -e 'sleep int(rand(43200))' && certbot -q renew
```

The script runs twice a day and renews certificates that will expire within 30 days.

To check the renewal process, we can execute the following command manually.

    certbot renew --dry-run

Now you will see what you put in the `index.html` but on the secure `https`

If you now view the nginx configuration again you will see that there have been newlines added automatically by the certbot -->

<!-- ## Setup frontend

We assume that the frontend is containerized and also uploaded to the users docker hub.
Simple pull the container as the project user and run it.

    docker pull <docker hub account>/<project_container_browser>:<version>

    docker run -d -p <port_project>:<port_nginx_configuration> <docker hub account>/<project_container_browser>:<version>

The port can be set to a desired port and you than update the nginx configuration as such. Make sure the project port is correct.

### update nginx configuration

Change the root location (and any specific frontend paths) like this

```
location / {
    proxy_pass          http://localhost:<port_project>;
    proxy_set_header    Host              $host;
    proxy_set_header    X-Real-IP         $remote_addr;
    proxy_set_header    X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header    X-Client-Verify   SUCCESS;
    proxy_set_header    X-Client-DN       $ssl_client_s_dn;
    proxy_set_header    X-SSL-Subject     $ssl_client_s_dn;
    proxy_set_header    X-SSL-Issuer      $ssl_client_i_dn;
    proxy_set_header    X-Forwarded-Proto http;
    proxy_read_timeout 1800;
    proxy_connect_timeout 1800;
}
```

reload nginx again and now you should see the container frontend.

If all the endpoints in fronend and backend are correctly set to the secure url set in the dns configuration it should now work.
The most important variables are `BASE_URL`, `FRONTEND_URL` and `ALLOWED_ORIGINS`. If they are set the basic functionality should be working. -->

10.105.203.174
