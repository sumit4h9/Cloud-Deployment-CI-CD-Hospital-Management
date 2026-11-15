#!/bin/bash
set -euo pipefail

# ==============================================================================
# Database Backup Procedure
# Targets PostgreSQL in Kubernetes / Docker or SQLite fallback
# ==============================================================================

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

echo "=== Starting Healthcare Platform Database Backup ==="

if command -v kubectl >/dev/null 2>&1 && kubectl get pod -n healthcare postgres-0 >/dev/null 2>&1; then
    echo "Detected Kubernetes PostgreSQL cluster in namespace 'healthcare'..."
    BACKUP_FILE="${BACKUP_DIR}/postgres_k8s_${TIMESTAMP}.dump"
    kubectl exec -n healthcare postgres-0 -c postgresql -- pg_dump -U clinic_admin -d appointments_db -F c -b -v -f /tmp/k8s_backup.dump
    kubectl cp healthcare/postgres-0:/tmp/k8s_backup.dump "$BACKUP_FILE"
    echo "Kubernetes backup successfully saved to: $BACKUP_FILE"

elif command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q appointment-database; then
    echo "Detected Docker Compose PostgreSQL container 'appointment-database'..."
    BACKUP_FILE="${BACKUP_DIR}/postgres_docker_${TIMESTAMP}.dump"
    docker exec -e PGPASSWORD=clinic_secure_pass_2026 appointment-database pg_dump -U clinic_admin -d appointments_db -F c -b -v -f /tmp/db_backup.dump
    docker cp appointment-database:/tmp/db_backup.dump "$BACKUP_FILE"
    echo "Docker backup successfully saved to: $BACKUP_FILE"

elif [ -f "appointments.db" ]; then
    echo "Backing up local SQLite database with WAL checkpoint..."
    BACKUP_FILE="${BACKUP_DIR}/sqlite_${TIMESTAMP}.db"
    python -c "
import sqlite3, shutil
conn = sqlite3.connect('appointments.db')
conn.execute('PRAGMA wal_checkpoint(TRUNCATE);')
conn.close()
shutil.copyfile('appointments.db', '$BACKUP_FILE')
print('SQLite database snapshotted successfully.')
"
    echo "Local backup successfully saved to: $BACKUP_FILE"
else
    echo "ERROR: No active database found to back up."
    exit 1
fi

echo "=== Backup Completed: $BACKUP_FILE ==="

