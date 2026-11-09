# PostgreSQL 16 + PostGIS 3 + pgvector, multi-arch (linux/amd64 and linux/arm64).
# The official postgis/postgis image publishes amd64 only, so this builds on the official
# multi-arch postgres image, which already ships the PGDG apt repository with matching
# PostGIS and pgvector packages. Debian trixie keeps glibc (and therefore collation order)
# identical to the previous postgis/postgis:16-3.6 base, so existing data volumes stay valid.
# Extensions (postgis, vector, pgcrypto, pg_trgm) are created by the Alembic migrations.
FROM postgres:16-trixie

ARG POSTGIS_MAJOR=3
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        "postgresql-${PG_MAJOR}-postgis-${POSTGIS_MAJOR}" \
        "postgresql-${PG_MAJOR}-postgis-${POSTGIS_MAJOR}-scripts" \
        "postgresql-${PG_MAJOR}-pgvector" \
    && rm -rf /var/lib/apt/lists/*
