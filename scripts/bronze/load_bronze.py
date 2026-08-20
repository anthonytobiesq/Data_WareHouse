from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "DataWarehouse.duckdb"

# Update these folder/file names to match where your source CSVs live
CSV_DIR = BASE_DIR / "datasets/source_crm"
CSV_DIR2 = BASE_DIR / "datasets/source_erp"


def load_bronze_data():
    with duckdb.connect(str(DB_PATH)) as conn:

        # Map each table to its corresponding CSV file path
        loads = [
            ("bronze.crm_cust_info", CSV_DIR / "cust_info.csv"),
            ("bronze.crm_prd_info", CSV_DIR / "prd_info.csv"),
            ("bronze.crm_sales_details", CSV_DIR / "sales_details.csv"),
            ("bronze.erp_loc_a101", CSV_DIR2 / "LOC_A101.csv"),
            ("bronze.erp_cust_az12", CSV_DIR2 / "CUST_AZ12.csv"),
            ("bronze.erp_px_cat_g1v2", CSV_DIR2 / "PX_CAT_G1V2.csv"),
        ]

        for table, csv_path in loads:
            if csv_path.exists():
                conn.sql(
                    f"COPY {table} FROM '{csv_path}' (HEADER, DELIMITER ',');"
                )
                count = conn.sql(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
                print(f"Loaded {count} rows into {table}")
            else:
                print(f"Warning: File not found at {csv_path}")


if __name__ == "__main__":
    load_bronze_data()