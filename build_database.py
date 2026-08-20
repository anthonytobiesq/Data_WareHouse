from pathlib import Path
import duckdb

# Ensures we hit the exact same file every time
db_path = Path(__file__).parent / "DataWarehouse.duckdb"
conn = duckdb.connect(str(db_path))

# 1. Create Schemas
conn.sql("CREATE SCHEMA IF NOT EXISTS bronze;")
conn.sql("CREATE SCHEMA IF NOT EXISTS silver;")
conn.sql("CREATE SCHEMA IF NOT EXISTS gold;")

# 2. List of individual table creation statements
statements = [
    # Table 1
    "DROP TABLE IF EXISTS bronze.crm_cust_info;",
    """CREATE TABLE bronze.crm_cust_info (
        cst_id INTEGER,
        cst_key VARCHAR,
        cst_firstname VARCHAR,
        cst_lastname VARCHAR,
        cst_marital_status VARCHAR,
        cst_gndr VARCHAR,
        cst_create_date DATE
    );""",
    # Table 2
    "DROP TABLE IF EXISTS bronze.crm_prd_info;",
    """CREATE TABLE bronze.crm_prd_info (
        prd_id INTEGER,
        prd_key VARCHAR,
        prd_nm VARCHAR,
        prd_cost INTEGER,
        prd_line VARCHAR,
        prd_start_dt TIMESTAMP,
        prd_end_dt TIMESTAMP
    );""",
    # Table 3
    "DROP TABLE IF EXISTS bronze.crm_sales_details;",
    """CREATE TABLE bronze.crm_sales_details (
        sls_ord_num VARCHAR,
        sls_prd_key VARCHAR,
        sls_cust_id INTEGER,
        sls_order_dt INTEGER,
        sls_ship_dt INTEGER,
        sls_due_dt INTEGER,
        sls_sales INTEGER,
        sls_quantity INTEGER,
        sls_price INTEGER
    );""",
    # Table 4
    "DROP TABLE IF EXISTS bronze.erp_loc_a101;",
    """CREATE TABLE bronze.erp_loc_a101 (
        cid VARCHAR,
        cntry VARCHAR
    );""",
    # Table 5
    "DROP TABLE IF EXISTS bronze.erp_cust_az12;",
    """CREATE TABLE bronze.erp_cust_az12 (
        cid VARCHAR,
        bdate DATE,
        gen VARCHAR
    );""",
    # Table 6
    "DROP TABLE IF EXISTS bronze.erp_px_cat_g1v2;",
    """CREATE TABLE bronze.erp_px_cat_g1v2 (
        id VARCHAR,
        cat VARCHAR,
        subcat VARCHAR,
        maintenance VARCHAR
    );""",
]

# Execute each query individually so DuckDB cannot skip anything
for stmt in statements:
    conn.sql(stmt)

print("\n--- VERIFICATION IN PYTHON ---")
print(conn.sql("SHOW ALL TABLES;"))

# Close to flush to disk
conn.close()