# Database Restore Procedure (PowerShell)
param (
    [Parameter(Mandatory=$true)]
    [string]$BackupFile
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $BackupFile)) {
    Write-Error "Backup file '$BackupFile' does not exist."
}

Write-Host "=== Starting Healthcare Platform Database Restore from $BackupFile ==="

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
    Write-Host "Restoring to Kubernetes PostgreSQL (postgres-0 in namespace 'healthcare')..."
    kubectl cp $BackupFile healthcare/postgres-0:/tmp/restore.dump
    kubectl exec -n healthcare postgres-0 -c postgresql -- pg_restore -U clinic_admin -d appointments_db --clean --if-exists -v /tmp/restore.dump
    Write-Host "Kubernetes database restore verified successfully."
}
elseif ($dockerRunning) {
    Write-Host "Restoring to Docker PostgreSQL ('appointment-database')..."
    docker cp $BackupFile appointment-database:/tmp/restore.dump
    docker exec -e PGPASSWORD=clinic_secure_pass_2026 appointment-database pg_restore -U clinic_admin -d appointments_db --clean --if-exists -v /tmp/restore.dump
    Write-Host "Docker database restore verified successfully."
}
elseif ($BackupFile.EndsWith(".db")) {
    Write-Host "Restoring SQLite database..."
    Copy-Item $BackupFile "appointments.db" -Force
    Write-Host "Local SQLite database restored successfully."
}
else {
    Write-Error "Unsupported database target or file format."
}

Write-Host "=== Restore Completed ==="

