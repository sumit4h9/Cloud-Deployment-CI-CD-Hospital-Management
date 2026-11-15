# Evidence 12: Database Backup and Restore Verification

### Backup Command:
```powershell
.\scripts\backup.ps1
```
*Output*:
```text
=== Starting Healthcare Platform Database Backup ===
Backing up database with WAL checkpoint...
Local backup successfully saved to: ./backups/sqlite_20261115_120000.db
=== Backup Completed ===
```

### Restore Verification:
```powershell
.\scripts\restore.ps1 -BackupFile "./backups/sqlite_20261115_120000.db"
```
*Output*:
```text
=== Starting Healthcare Platform Database Restore from ./backups/sqlite_20261115_120000.db ===
Restoring SQLite database...
Local SQLite database restored successfully.
=== Restore Completed ===
```

*Record Integrity Verification*:
- Synthetic patient and doctor appointment records were queried before and after restore.
- Verified that synthetic patient consultations (`Patient #1042`, `Patient #1014`, `Dr. Ananya Mehta`) match exact pre-backup snapshot state.

Status: **PASS**

