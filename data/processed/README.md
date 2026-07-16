# Processed Data Folder

Owner: Monesh

This folder stores generated data-layer outputs from the ingestion pipeline.

## Planned Outputs

- `learner_dropoff.sqlite`: SQLite database created from the schema in `src/database/schema.sql`.
- `learner_course_aggregates.csv`: learner-course feature input generated for Shaswath's analysis lane.
- Future aggregate exports for Shaswath's analysis lane, if needed.

Generated database files should be rebuilt from raw data and scripts. Avoid manual edits to processed outputs.

## Aggregate Generation Command

After loading raw CSV files into SQLite, generate the analysis handoff CSV with:

```bash
python src/database/build_aggregates.py
```
