# Database Backup Procedure (PowerShell)
param (
    [string]$BackupDir = "./backups"
)

$ErrorActionPreference = "Stop"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

Write-Host "=== Starting Healthcare Platform Database Backup ==="

$k8sRunning = $false
try {
    $res = kubectl get pod -n healthcare postgres-0 2>$null
    if ($LASTEXITCODE -eq 0) { $k8sRunning = $true }
} catch {}

$dockerRunning = $false
try {
    $containers = docker ps --format '{{.Names}}' 2>$null
    if ($containers -match "appointment-database") { $dockerRunning = $true }
} catch {}

if ($k8sRunning) {
    Write-Host "Detected Kubernetes PostgreSQL cluster in namespace 'healthcare'..."
    $backupFile = "$BackupDir/postgres_k8s_$Timestamp.dump"
    kubectl exec -n healthcare postgres-0 -c postgresql -- pg_dump -U clinic_admin -d appointments_db -F c -b -v -f /tmp/k8s_backup.dump
    kubectl cp healthcare/postgres-0:/tmp/k8s_backup.dump $backupFile
    Write-Host "Kubernetes backup successfully saved to: $backupFile"
}
elseif ($dockerRunning) {
    Write-Host "Detected Docker Compose PostgreSQL container 'appointment-database'..."
    $backupFile = "$BackupDir/postgres_docker_$Timestamp.dump"
    docker exec -e PGPASSWORD=clinic_secure_pass_2026 appointment-database pg_dump -U clinic_admin -d appointments_db -F c -b -v -f /tmp/db_backup.dump
    docker cp appointment-database:/tmp/db_backup.dump $backupFile
    Write-Host "Docker backup successfully saved to: $backupFile"
}
elseif (Test-Path "appointments.db") {
    Write-Host "Backing up local SQLite database with WAL checkpoint..."
    $backupFile = "$BackupDir/sqlite_$Timestamp.db"
    python -c @"
import sqlite3, shutil
conn = sqlite3.connect('appointments.db')
conn.execute('PRAGMA wal_checkpoint(TRUNCATE);')
conn.close()
shutil.copyfile('appointments.db', r'$backupFile')
print('SQLite database snapshotted successfully.')
"@
    Write-Host "Local backup successfully saved to: $backupFile"
}
else {
    Write-Error "No active database found to back up."
}

Write-Host "=== Backup Completed ==="

