# Processed Data Folder

Owner: Monesh

This folder stores generated data-layer outputs from the ingestion pipeline.

## Planned Outputs

- `learner_dropoff.sqlite`: SQLite database created from the schema in `src/database/schema.sql`.
- Future aggregate exports for Shaswath's analysis lane, if needed.

Generated database files should be rebuilt from raw data and scripts. Avoid manual edits to processed outputs.
