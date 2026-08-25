# Data_WareHouse (WIP)

A small DuckDB data warehouse project that demonstrates a layered data pipeline from raw CRM and ERP CSV files to cleaned, analytics-ready views.

## Project Status

The core Bronze, Silver, and Gold pipeline is in progress. The project diagrams have **not been created yet** and remain an outstanding documentation task:

- [ ] Add the warehouse architecture diagram
- [ ] Add the source-to-target data flow diagram
- [ ] Add the Gold layer star schema/data model diagram

## Architecture

The warehouse uses three layers:

1. **Bronze**: Raw CRM and ERP data loaded from CSV files.
2. **Silver**: Cleaned and standardized tables, including normalized dates, labels, keys, and calculated values.
3. **Gold**: Analytics-ready views consisting of customer and product dimensions plus the sales fact table.

The database is stored locally in `DataWarehouse.duckdb` and is managed with DuckDB.

## Source Data

- `datasets/source_crm/`
	- Customer information
	- Product information
	- Sales details
- `datasets/source_erp/`
	- Customer demographics
	- Customer locations
	- Product categories

## Pipeline Scripts

Run the scripts from the repository root in this order:

```bash
python build_database.py
python scripts/bronze/load_bronze.py
python scripts/silver/transform_silver.py
python scripts/gold/gold_layer.py
python tests/run_quality_checks.py
```

`build_database.py` creates the schemas and Bronze table structures. The Bronze, Silver, and Gold scripts then load, transform, and expose the data in stages. The quality-check script validates Silver data rules and includes Gold checks that can be enabled when needed.

## Requirements

Python 3.13 or newer is required. The pinned project requirements are recorded in [`uv.lock`](uv.lock); currently the lockfile resolves the DuckDB Python package to version `1.5.5`.

Install the locked dependencies with `uv`:

```bash
uv sync
```

After syncing, run the pipeline with `uv run` so each script uses the locked environment:

```bash
uv run python build_database.py
uv run python scripts/bronze/load_bronze.py
uv run python scripts/silver/transform_silver.py
uv run python scripts/gold/gold_layer.py
uv run python tests/run_quality_checks.py
```

If `uv` is not available, the dependency declaration in `pyproject.toml` can also be installed with `pip install -e .`; `uv.lock` remains the authoritative file for reproducible versions.

## Repository Layout

```text
build_database.py          # Create schemas and Bronze tables
DataWarehouse.duckdb       # Local DuckDB database
datasets/                  # CRM and ERP source CSV files
scripts/bronze/            # Raw data loading
scripts/silver/            # Cleaning and standardization
scripts/gold/              # Analytics-ready views
tests/                     # Data quality checks
docs/                      # Project documentation and future diagrams
```

