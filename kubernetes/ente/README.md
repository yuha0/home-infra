# Ente Photos

Self-hosted [Ente](https://ente.com/help/self-hosting) photo backup.

## Backups

Not fully implemented yet but the plan is:

[] **Postgres**: cnpg auto backup to seaweedfs (and further uploaded to colder tier, see below)
[] **The `ente` object storage bucket**: seaweedfs tiered storage (cloud deep archive)
[x] **`museum-keys`**: 1Password
