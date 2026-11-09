#!/bin/sh
# Restore a Gonarra dump into the production database. Run from the repository root on the VM:
#
#   infra/backup/restore.sh gonarra-20261109T200000Z.dump
#
# The file name is looked up in the gonarra backups volume (as listed by
#   docker compose -f docker-compose.prod.yml exec backup ls -lh /backups).
# Steps: stop api (no writes during restore) -> drop and recreate the database (so tables created
# after the dump do not survive) -> pg_restore in a single transaction -> run migrations (a dump
# older than the current code is brought to head) -> start api.
set -eu

if [ $# -ne 1 ]; then
    echo "usage: $0 <dump file name in /backups>" >&2
    exit 2
fi
DUMP="$1"
COMPOSE="${COMPOSE:-docker compose -f docker-compose.prod.yml}"

$COMPOSE exec -T backup test -f "/backups/$DUMP" </dev/null || { echo "no such dump: /backups/$DUMP" >&2; exit 1; }

printf 'Restore /backups/%s over the live database? This replaces all data. [type yes] ' "$DUMP"
read -r answer || answer=""
[ "$answer" = "yes" ] || { echo "aborted"; exit 1; }

$COMPOSE stop api
# The backup container has the PG* connection variables and the backups volume mounted.
$COMPOSE exec -T -e DUMP="$DUMP" backup sh -c \
    'set -e
     dropdb --maintenance-db=postgres --force --if-exists "$PGDATABASE"
     createdb --maintenance-db=postgres --owner="$PGUSER" "$PGDATABASE"
     pg_restore --no-owner --single-transaction --exit-on-error \
         --dbname="$PGDATABASE" "/backups/$DUMP"' </dev/null
$COMPOSE run --rm migrate </dev/null
$COMPOSE start api
echo "restored $DUMP; check: curl -fsS https://\$GONARRA_API_HOST/ready"
