#!/bin/bash
set -e

echo "=== Initializing TANPHAT ONE Database ==="
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE tp_tanphat_dev OWNER tp_odoo;
EOSQL

echo "=== Restoring Full Database Dump ==="
pg_restore --username "$POSTGRES_USER" --dbname tp_tanphat_dev --no-owner /latest_deploy_full.dump || true
echo "=== Database Restore Complete ==="
