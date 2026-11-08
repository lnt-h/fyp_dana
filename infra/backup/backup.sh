#!/bin/sh
# Nightly logical backup of the Gonarra database (QAS-08: RPO 24 h, RTO 4 h).
#
#   backup.sh          loop: one dump per day at BACKUP_HOUR (TZ), forever (compose service)
#   backup.sh once     one dump now, then exit (manual / host cron)
#
# Dumps are custom-format (pg_dump -Fc), written atomically to BACKUP_DIR, checked with
# pg_restore --list, and kept for BACKUP_RETENTION_DAYS days. Connection settings come from
# the standard libpq variables PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE.
# The volume lives on the same disk as the database: copy dumps off the VM as well (infra/README.md).
set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_HOUR="${BACKUP_HOUR:-3}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) backup: $*"; }

dump_once() {
    mkdir -p "$BACKUP_DIR"
    stamp="$(date -u +%Y%m%dT%H%M%SZ)"
    final="$BACKUP_DIR/${PGDATABASE:-gonarra}-$stamp.dump"
    tmp="$final.partial"
    log "dumping ${PGDATABASE:-gonarra} to $final"
    if ! pg_dump --format=custom --compress=6 --no-owner --file="$tmp"; then
        rm -f "$tmp"
        log "FAILED: pg_dump"
        return 1
    fi
    if ! pg_restore --list "$tmp" >/dev/null; then
        rm -f "$tmp"
        log "FAILED: dump is not readable by pg_restore"
        return 1
    fi
    mv "$tmp" "$final"
    log "ok $(du -h "$final" | cut -f1)"
    # Rotation: delete dumps (and stale partials) older than the retention window.
    find "$BACKUP_DIR" -maxdepth 1 -type f \( -name '*.dump' -o -name '*.dump.partial' \) \
        -mtime "+$((BACKUP_RETENTION_DAYS - 1))" -print -delete | sed 's/^/deleted /'
}

seconds_until_next_run() {
    now=$(date +%s)
    next=$(date -d "$(date +%Y-%m-%d) ${BACKUP_HOUR}:00:00" +%s)
    if [ "$next" -le "$now" ]; then
        next=$((next + 86400))
    fi
    echo $((next - now))
}

if [ "${1:-loop}" = "once" ]; then
    dump_once
    exit $?
fi

log "scheduler started: daily at ${BACKUP_HOUR}:00 ${TZ:-UTC}, keep ${BACKUP_RETENTION_DAYS} days"
while true; do
    wait_s=$(seconds_until_next_run)
    log "next dump in ${wait_s}s"
    sleep "$wait_s"
    # A failed night is logged and retried the next night; the loop never exits on failure.
    dump_once || true
done
