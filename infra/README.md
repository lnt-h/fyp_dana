# Gonarra deployment runbook (single VM)

One VM runs `docker-compose.prod.yml`: **caddy** (automatic HTTPS, the only service with host
ports) → **api** (FastAPI, non-root, `GONARRA_ENVIRONMENT=production` pinned) → **db**
(PostgreSQL 16 + PostGIS + pgvector, no published port), plus a one-shot **migrate** job
(`alembic upgrade head`; api starts only after it exits 0) and a **backup** job (nightly
`pg_dump -Fc`, 14-day rotation). This is the single-VM variant of ADR-002 that OQ-129 still has
to confirm; with RDS, point `GONARRA_DATABASE_URL` at RDS in an override file and drop `db`/`backup`.

All images are built on the VM for its own architecture (arm64 on EC2 t4g, amd64 elsewhere).
`infra/postgres` builds PostGIS + pgvector on the official multi-arch `postgres:16-trixie` image.

| File | Purpose |
|---|---|
| `docker-compose.prod.yml` | Production stack |
| `infra/.env.example` | Template for the VM's `./.env` (secrets, host name, backup schedule) |
| `infra/Caddyfile` | TLS, reverse proxy, security headers, access log without query strings |
| `infra/backup/backup.sh` | Nightly dump loop (`once` for a manual dump) |
| `infra/backup/restore.sh` | Interactive restore of one dump |
| `infra/postgres/Dockerfile` | Multi-arch PostgreSQL 16 + PostGIS 3 + pgvector |
| `infra/dev.env` | Development defaults for the local `docker-compose.yml` only |

Below, `dc` means `docker compose -f docker-compose.prod.yml` (run from the repository root).

## First deploy (fresh Ubuntu 24.04 VM)

1. DNS: create an A (and AAAA, if used) record for the API host pointing at the VM.
   Firewall / security group: allow inbound 22 (or SSM only), 80/tcp, 443/tcp, 443/udp.
2. Install Docker Engine and the Compose plugin (official repository):
   ```sh
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker "$USER" && newgrp docker
   docker compose version          # v2.24+ required (env_file "required:" syntax)
   ```
3. Get the code and create the env file:
   ```sh
   sudo mkdir -p /opt/gonarra && sudo chown "$USER" /opt/gonarra
   git clone https://github.com/lnt-h/fyp_dana.git /opt/gonarra && cd /opt/gonarra
   cp infra/.env.example .env && chmod 600 .env
   sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=')|" .env
   $EDITOR .env                     # GONARRA_API_HOST, ACME_EMAIL, Clerk and provider keys
   ```
4. Build and start:
   ```sh
   export GONARRA_API_TAG=$(git rev-parse --short HEAD)
   dc up -d --build --wait
   dc ps                            # migrate: Exited (0); db, api: healthy; caddy, backup: running
   curl -fsS https://<GONARRA_API_HOST>/ready
   ```
5. Seed and run the catalog pipeline with the API image, e.g. `dc run --rm --no-deps api python -m app.cli seed`
   (any Typer command works the same way; `api` has internet access, `migrate` does not; see `apps/api/README.md`).

`POSTGRES_PASSWORD` is used only when the database volume is first initialised; changing it later
needs `ALTER USER gonarra PASSWORD '...'` inside the db as well.

## Update

```sh
cd /opt/gonarra && git pull
export GONARRA_API_TAG=$(git rev-parse --short HEAD)
dc exec backup /bin/sh /usr/local/bin/gonarra-backup.sh once   # pre-deploy dump
dc up -d --build --wait          # rebuilds, runs migrate, then recreates api
```

Caddy retries the upstream for 15 s, so the short api restart shows as a slow request, not a 502.
There is no zero-downtime deploy (accepted in ADR-002). Caddy picks up `infra/Caddyfile` changes
with `dc exec caddy caddy reload --config /etc/caddy/Caddyfile`.

## Rollback

Images are tagged by commit, so the previous image is still on the VM (`docker images gonarra-api`).

```sh
GONARRA_API_TAG=<previous sha> dc up -d --no-build --no-deps api
```

`--no-deps` skips `migrate`: old code cannot "upgrade" a database that is already at a newer revision.

This rolls back code only. If the bad release ran a migration the old code cannot use, either
downgrade it with the new image first (`dc run --rm migrate alembic downgrade <revision>`) or
restore the pre-deploy dump (below). Keep `git checkout <previous sha>` for compose/Caddy changes.

## Backups and restore

- `backup` dumps nightly at `BACKUP_HOUR` (`BACKUP_TZ`, default 03:00 Asia/Ho_Chi_Minh) to the
  `backups` volume, checks each dump with `pg_restore --list`, and deletes dumps older than
  `BACKUP_RETENTION_DAYS` (14). Watch it with `dc logs backup`.
- List: `dc exec backup ls -lh /backups`. Manual dump: `dc exec backup /bin/sh /usr/local/bin/gonarra-backup.sh once`.
- The volume is on the VM disk. For RPO 24 h against loss of the VM, copy dumps off-host, e.g. a
  daily host cron: `docker cp "$(dc ps -q backup)":/backups ./backups-copy && aws s3 sync ./backups-copy s3://<bucket>/gonarra/`
  (or EBS snapshots). Rehearse a restore before the study (ADR-002 follow-up).
- Restore (stops api, drops and recreates the database, `pg_restore`, migrates to head, starts api):
  ```sh
  infra/backup/restore.sh gonarra-20261109T200000Z.dump     # asks you to type "yes"
  ```
  To restore a dump copied from elsewhere: `docker cp file.dump "$(dc ps -q backup)":/backups/` first.

## Logs and health

```sh
dc ps                              # health status of every service
dc logs -f --tail=100 api          # application log (no uvicorn access log)
dc logs -f caddy                   # JSON access log; query strings redacted, auth headers redacted
dc logs migrate                    # last migration run
```

Container logs rotate at 10 MB × 5 files per service. `/health` is liveness, `/ready` checks the
database; Docker marks api unhealthy after three failed `/ready` probes and `restart: unless-stopped`
brings crashed containers (and all services after a VM reboot) back.

## Smoke test without a public host name

```sh
cp infra/.env.example /tmp/prodtest.env    # set POSTGRES_PASSWORD, GONARRA_API_HOST=api.gonarra.test,
                                           # GONARRA_TLS_MODE=internal, GONARRA_ENV_FILE=/tmp/prodtest.env,
                                           # GONARRA_HTTP_PORT=18080, GONARRA_HTTPS_PORT=18443
docker compose -p gonarra-prodtest -f docker-compose.prod.yml --env-file /tmp/prodtest.env up -d --build --wait
curl -k --resolve api.gonarra.test:18443:127.0.0.1 https://api.gonarra.test:18443/ready
docker compose -p gonarra-prodtest -f docker-compose.prod.yml --env-file /tmp/prodtest.env down -v
```
