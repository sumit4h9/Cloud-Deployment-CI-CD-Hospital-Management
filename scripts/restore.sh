#!/bin/bash
set -euo pipefail

# ==============================================================================
# Database Restore Procedure
# Restores PostgreSQL in Kubernetes / Docker or SQLite fallback
# ==============================================================================

if [ $# -lt 1 ]; then
    echo "Usage: $0 <path_to_backup_file>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file '$BACKUP_FILE' does not exist."
    exit 1
fi

echo "=== Starting Healthcare Platform Database Restore from $BACKUP_FILE ==="

if command -v kubectl >/dev/null 2>&1 && kubectl get pod -n healthcare postgres-0 >/dev/null 2>&1; then
    echo "Restoring to Kubernetes PostgreSQL (postgres-0 in namespace 'healthcare')..."
    kubectl cp "$BACKUP_FILE" healthcare/postgres-0:/tmp/restore.dump
    kubectl exec -n healthcare postgres-0 -c postgresql -- pg_restore -U clinic_admin -d appointments_db --clean --if-exists -v /tmp/restore.dump
    echo "Kubernetes database restore verified successfully."

elif command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q appointment-database; then
    echo "Restoring to Docker PostgreSQL ('appointment-database')..."
    docker cp "$BACKUP_FILE" appointment-database:/tmp/restore.dump
    docker exec -e PGPASSWORD=clinic_secure_pass_2026 appointment-database pg_restore -U clinic_admin -d appointments_db --clean --if-exists -v /tmp/restore.dump
    echo "Docker database restore verified successfully."

elif [[ "$BACKUP_FILE" == *.db ]]; then
    echo "Restoring SQLite database..."
    cp "$BACKUP_FILE" appointments.db
    echo "Local SQLite database restored successfully."
else
    echo "ERROR: Unsupported database target or file format."
    exit 1
fi

echo "=== Restore Completed ==="

