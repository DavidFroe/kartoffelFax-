# Migrations

`schema.sql` (one directory up) is the authoritative, idempotent baseline schema
(`CREATE TABLE IF NOT EXISTS ...`) and is applied on every startup via
`database.init_db()`.

Once the schema needs a breaking change after the first release, add a numbered
file here (e.g. `0002_add_cover_sheet.sql`) with the `ALTER TABLE` / data
migration statements, and apply it before `schema.sql` in `init_db()`,
recording it in `schema_migrations`. Until then this directory stays empty.
