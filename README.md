# pixelfed-docker

This repo contains an opinionated build system to run a pixelfed instance. Some of the main benefits include:

- Automatic SSL certificates
- A fully working run-locally setup so you can test new updates/changes before pushing to prod
- Automatic backups
- Mechanism for cloning data from prod -> dev to test changes
- Well-defined folders for secrets, to prevent accidental disclosure of keys

Best of all, the primary setup is a run-once scaffolding. That means that you can customize the setup to your heart's content. Just take the generated configs, and tweak until you have the setup you're comfortable with. Even though the setup is opinionated, it's easy to change, since there's no runtime component to the scripting (only docker images). For more details, see the [How it Works](#how-it-works) section

## Why?

Running pixelfed actually takes a lot of work. Even though there are some scripts and built-in docker files, there's a lot to configure and manage on your own. SSL certificates, keeping the php, redis, and worker configs compatible. Having different settings to debug problems vs. prod, and the list goes on. I found the experience to be very much NOT turnkey, and hence this repo exists to make the admin experience as turnkey as possible.

# Getting started

The way this works is you need to get some prerequisites ready (get your S3 buckets ready, etc.) Then, when you run the [scaffold](./scaffold.py) program, it will ask you a bunch of questions, save your responses, and then finally generate all of the config files needed to power your experience. You can then run pixelfed locally, and make sure everything works well. Finally, you can copy all of the files to your remote webhost, and run the prod version.

# Prerequisites

- Install Docker, git, and python3 on your computer
- Create a free [ngrok](https://ngrok.com/) account, and have your [ngrok authtoken](https://dashboard.ngrok.com/get-started/setup) available
  - Ngrok is used only for local development, since we need a proper URL to view pixelfed
  - There are paid versions of ngrok, but this setup works with the free version.
- Create an account with an S3-compatible webhost. I strongly encourage you to not give money to Amazon. If you're not sure, maybe try [backblaze](https://www.backblaze.com)?
  - Create two buckes (pixelfed, and pixelfed-dev) that are configured to allow PUBLIC access to the files. (The names are just references, you can call them whatever makes sense to you and is available)
  - Create a third bucket (pixelfed-backups), but make sure that bucket is private
  - Create 3 API keys - one key that can read/write to pixelfed, another key that can read/write to pixelfed-dev, and a third key that can read/write to all three buckets (for your backups)
  - Make note of the following pieces of information for your S3 API. If using backblaze, see [their docs](https://help.backblaze.com/hc/en-us/articles/360047425453-Getting-Started-with-the-S3-Compatible-API) for the particulars
    - The endpoint URL
    - The region
    - The AWS access key (e.g. the api key userid)
    - The AWS secret access key (e.g. the password for the api key)

# Installation

1. Download the repository, including the pixelfed submodule: `git clone --recurse-submodules`
1. `cd pixelfed-docker`
1. Create a virtual environment for python `python -m venv ./env`
1. Use the environment `source ./env/bin/activate`
1. Install the python packages needed for the scripts: `pip install -r requirements.txt`

# Generating the initial scaffolding

1. In the python environment (see the [Installation](#installation) steps), execute `./scaffold.py`. This will ask you a bunch of questions. Enter your answers on the command line and hit enter. You'll need the steps from the [Prerequisites](#prerequisites) to complete the config
1. Once you answer all of the necessary questions, the code will generate the scaffolding you need
1. Run the one-time setup tasks: `docker compose --profile setup run initialize`
1. Run the dev server: `docker compose --profile dev up`
1. Wait a minute for everything to build and start
1. Navigate to https://localhost:8000
   - Note that the ngrok URL will change every time. But you can always go to this localhost address to find it
1. Enter in the admin username & password from earlier
1. Do whatever you need to in order to test the changes locally

# Deploy to Prod

1. Figure out how to copy the directory to your remote webserver. For example, you could run `rsync -av pixelfed-docker user@yourwebhost.com:/home/user/pixelfed-docker`, or similar
1. Open an SSH tunnel to your webhost. Type the remaining commands in your SSH tunnel
1. `cd pixelfed-docker` (wherever you copied it to)
1. `docker compose --profile setup build`
1. `docker compose --profile setup run initialize`
1. `docker compose --profile prod up`1
1. Navigate to your website. When you first visit, you might get a SSL warning about self-signed certificates. Wait 2-5 minutes for the registration to automatically finish
1. Refresh your browser after 5 minutes and the SSL certificate should be installed
1. Figure out how to autostart docker on your webhost. For example:

```
[Unit]
Description=Pixelfed docker compose
Requires=docker.service
After=docker.service

[Service]
WorkingDirectory=/home/your_name_here/pixelfed-docker
ExecStart=/usr/bin/docker compose --profile prod up
ExecStartPost=/usr/bin/docker system prune -f
ExecStop=/usr/bin/docker compose --profile prod down
TimeoutStartSec=0
Restart=on-failure
StartLimitIntervalSec=60
StartLimitBurst=3

[Install]
WantedBy=multi-user.target

```

# Updating pixelfed

The nice thing about this setup is you can test the changes locally to your hearts content before deploying!

1. Back in your local terminal, `cd pixelfed-docker/pixelfed`
1. Update the git repository to the appropriate commit you're interested in. E.g `git pull origin dev`
1. Re-build the pixelfed base image `docker compose --profile setup build pixelfed`
1. Re-build the dev environment `docker compose --profile dev build`
1. Run the worker in docker `docker compose --profile dev run --rm -i -t worker /bin/sh`
1. Switch to the www-data user: `su www-data`
1. Do any upgrade steps you need to, such as upgrading the database: `php artisan migrate --force`
1. Exit the custom worker
1. Test the changes `docker compose --profile dev up`
1. Copy the files over to your prod webserver.
1. Run the same steps on prod, except use `--profile prod`

# Auto Backups

The [docker-compose.yml](./docker-compose.yml) file contains a backup service. This service runs daily and backs up the database files, as well as your S3 bucket. You don't need to do anything. It will delete old backups so you don't keep taking up space. The backups also run for the dev environment, so you can test it out and any changes locally, before deploying to prod

# Cloning prod data to dev

Sometimes, you might have an issue that only shows with real data and you need to investigate. You can use the backups system to make your local environment have the same posts, etc. as prod

1. `docker compose --profile dev run --rm backup_dev /root/restore.sh --source-environment=prod --dest-environment=dev -n=1 --restore-db --restore-s3`
1. Delete all your redis data. `docker system prune` followed by `docker volume rm <your redis volume name>` should do it
1. `docker compose --profile dev up`

# Restoring prod from a backup

It's very similar to the clone step, except you might not need to delete redis (unclear)

1. TAKE PROPER BACKUPS
1. `docker compose --profile prod run --rm backup /root/restore.sh --source-environment=prod -n=1 --restore-db --restore-s3`
1. Restart your instance

# How it works

![Display of how the docker containers work together. There's nginx, the app, and a worker. These are supported by the filesystem, and S3](./arch.png 'Architecture diagram')

Scaffold.py works in two stages. First, it loads the existing configuration from [config/config.toml](./config/config.toml) and [secrets/config.toml](./secrets/config.toml). If any settings are missing, it prompts the user, then saves them to the appropriate file. (The reason there are two config files is that the latter one contains stuff you don't want others to see. Passwords, etc. You should never upload that folder to github). The scaffold.py can also generate some of the config for you - For example, it runs pixelfed to generate the oauth keys and other app secrets.

Then, the scaffold.py script takes the files in the [templates](./templates/) folder, replaces the variables with the ones from the config, and saves the new files to the appropriate locations. That's it for the scaffolding!

# Running Locally

If you try to run pixelfed and visit it from http://localhost, it just won't work. Pixelfed needs a domain to work properly. Ngrok is great, because we can have a domain name, but it's powered by our local computer. There's only one catch. If you don't pay for ngrok, then your domain name changes every time. As a workaround, the repo contains the [app_dynamic_domain](./config/app_dynamic_domain/app.py) docker image which updates the pixelfed env files to use the new domain automatically during startup. Lastly, we need to refresh the pixelfed config to pick up the new environment. There's a [pending PR](https://github.com/pixelfed/pixelfed/pull/4255) to handle this better, but in the mean time this is why the docker-compose file specifies the run command for the worker

# SSL certificates

The scaffolding uses the stateless version of the [http challenge](https://letsencrypt.org/docs/challenge-types/#http-01-challenge) to generate your certs. This means we can do in in two steps.

First, when running the scaffold.py, the script connects with LetsEncrypt, and registers a new account. When you register, you get two things: A private key, as well as an account_thumbprint. The account thumbprint is a string that needs to get returned by the webserver when you visit [your-domain]/.well-known/acme-challenge. Since this thumbprint is the same no matter what, we can just use the [nginx template](./templates/nginx.conf) to respond appropriately.

Then, when you run nginx on the prod account, it initially configures itself with self-signed certs (just to get started). It then starts the server, so that way nginx can begin responding to .well-known requests. A [cron job](./config/nginx/create_certs.sh) inside of the nginx container detects that no certs have been created. It then uses the registration information uploaded from the scaffolding to generate the certificate. Finally, the nginx configuration is reloaded, and the certs are up and running!

# Backups

It's just a cron job that runs `aws s3 cp <BUCKET> <BACKUP_BUCKET>` and `pg_dump | aws s3 cp` to copy both the files and the database. Then, there's a little bit of scripting to check how many existing backups exist, and to delete old ones. Nothing too fancy

# PHP

The primary code when responding to the website is in the `app` worker. This contains the main php response. Some things take longer to process, and that's what the worker is for. It uses jobs on redis to know when there's work to complete. All of the PHP containers use the same UID for `www-data` so there's no confusion with file ownership on what the permissions refer to
