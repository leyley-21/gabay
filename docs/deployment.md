# Deployment

The release is prepared for deployment; it is not already hosted. Choose a server
or Python hosting service, then configure a persistent directory and HTTPS domain.

## Python service (Windows or Linux)

1. Extract the release, create a virtual environment, and install requirements as
   shown in the README.
2. Configure environment variables for the service. Use a new DB file for a new
   public service, or restore your existing backed-up DB for an upgrade.
3. Initialize the DB using that same environment and start the service.

Example Linux shell:

```sh
export GABAY_DATABASE_PATH=/srv/als_gabay/data/production.db
export HOST=127.0.0.1
export PORT=8080
python manage.py initialize-database
python serve.py
```

On Windows, use `set VARIABLE=value` in Command Prompt or `$env:VARIABLE="value"`
in PowerShell. Ensure the service user can write to the DB's parent folder.
Use your host's service manager to restart the process after reboot or failure.

A host that expects a WSGI target can use `wsgi:application`. A host that expects a
start command can use `python serve.py`. Configure `HOST=0.0.0.0` if the hosting
platform routes requests into its own container, and honor its injected `PORT`.
Run `python manage.py initialize-database` during setup before serving.

The local default is port 8080. A process reporting that it started does not set up
a public domain or TLS certificate. Point your domain's DNS to the server and
configure the hosting HTTPS proxy. `deployment/Caddyfile.example` gives a simple
Caddy reverse-proxy example; replace its placeholder domain. Keep debug mode off.

Flask's official documentation describes Waitress as a production WSGI server
that supports Windows directly: https://flask.palletsprojects.com/en/stable/deploying/waitress/

## Docker Compose

Install Docker with Compose, then from the project root:

```sh
docker compose -f deployment/compose.yaml up --build -d
docker compose -f deployment/compose.yaml logs -f web
```

Open `http://localhost:8080`. Compose creates a named volume for the SQLite DB.
The image runs as a non-root user and initializes a new DB from the CSVs, without
copying the bundled demo database. Container restarts preserve volume data. Do not
run `docker compose down -v` unless you intend to delete that volume's data.
Put an HTTPS reverse proxy in front for public use.

For an HTTPS proxy on the same host, prefer binding the Compose port to localhost:
change `8080:8080` to `127.0.0.1:8080:8080` in `deployment/compose.yaml`.

## Storage and scaling

- Set `GABAY_DATABASE_PATH` to a file on a **persistent local disk/volume**.
  A hosting service's temporary filesystem can erase DB changes on redeploy.
- Use one application instance for this SQLite deployment. Waitress provides
  multiple threads. Multiple independent replicas with local DB copies do not
  share data. A larger deployment needs a separate shared-database design.
- Do not place the DB on a public/static directory or expose it as a download.
- `/health` checks that the occupation catalog is available. Configure the host's
  HTTP health probe to use that path.
- No login is implemented. Anonymous feedback is not identity-verified, so community
  influence is bounded. This service does not include administrator account management.

## Data review before launch

The three CSVs carry legacy estimates. Review institution-specific program
availability and current Philippine pay data for your target audience before
promoting those fields as verified guidance. Use the source/status/date fields;
see `docs/data_dictionary.md`. This is a content review item, separate from the
server's ability to run.

The custom questionnaire is exploratory guidance and has no demonstrated accuracy
rate. Scores are not probabilities, qualifications, or guarantees of employment.

## Upgrades and backups

Stop the app, back up the live DB and reference CSVs, install the new release,
then run `python manage.py initialize-database` with the existing DB path. Review
reference CSV edits before initialization because it reimports them. Restart
Waitress and check `/health` plus a test assessment.

To back up Docker data, stop the service before copying the DB out of the named
volume. Restore it to the same path and owner before restarting. Keep backups
outside the public web root. Do not overwrite a newer live DB with the release's
bundled demo file.

## Verification scope

Python integration tests and the Waitress/browser walkthrough were run on Linux
with Python 3.12. Windows/macOS and Docker deployment files are provided but were
not executed on those platforms in this environment. There is no published URL
or cloud-account deployment associated with this release.
