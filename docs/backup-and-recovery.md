# Backup and Recovery

PostgreSQL backups must be encrypted and access-controlled. Test restoration regularly into an isolated environment.

Application database backup example:
`pg_dump --format=custom --file=dps.dump "$DATABASE_URL"`

Restore example:
`pg_restore --clean --if-exists --dbname="$DATABASE_URL" dps.dump`

Audio files are separate from the database. The production object-storage design must use versioning or an approved backup strategy and must document deletion/retention interactions. Local demo audio under `storage/` is not a disaster-recovery solution.

Recovery objectives must be selected by DPS. Do not claim a specific RPO/RTO until measured and approved.
