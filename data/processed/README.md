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
python -m src.database.build_aggregates
```

## Full Data Pipeline Command

To run ingestion, data quality validation, and aggregate export together:

```bash
python -m src.ingestion.run_data_pipeline
```

Use strict mode when the real raw dataset is available and all expected files must be present:

```bash
python -m src.ingestion.run_data_pipeline --strict-raw
```
