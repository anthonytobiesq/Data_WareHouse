from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "DataWarehouse.duckdb"


def init_silver_tables(conn):
    print(" 1. Creating silver schema and tables...")
    ddl_script = """
    CREATE SCHEMA IF NOT EXISTS silver;
        
    CREATE TABLE IF NOT EXISTS silver.crm_cust_info (
        cst_id INT,
        cst_key VARCHAR(50),
        cst_firstname VARCHAR(50),
        cst_lastname VARCHAR(50),
        cst_marital_status VARCHAR(50),
        cst_gndr VARCHAR(50),
        cst_create_date DATE,
        dwh_create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS silver.crm_prd_info (
        prd_id INT,
        cat_id VARCHAR(50),
        prd_key VARCHAR(50),
        prd_nm VARCHAR(50),
        prd_cost INT,
        prd_line VARCHAR(50),
        prd_start_dt DATE,
        prd_end_dt DATE,
        dwh_create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS silver.crm_sales_details (
        sls_ord_num VARCHAR(50),
        sls_prd_key VARCHAR(50),
        sls_cust_id INT,
        sls_order_dt DATE,
        sls_ship_dt DATE,
        sls_due_dt DATE,
        sls_sales INT,
        sls_quantity INT,
        sls_price INT,
        dwh_create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS silver.erp_loc_a101 (
        cid VARCHAR(50),
        cntry VARCHAR(50),
        dwh_create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS silver.erp_cust_az12 (
        cid VARCHAR(50),
        bdate DATE,
        gen VARCHAR(50),
        dwh_create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS silver.erp_px_cat_g1v2 (
        id VARCHAR(50),
        cat VARCHAR(50),
        subcat VARCHAR(50),
        maintenance VARCHAR(50),
        dwh_create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn.sql(ddl_script)

def load_crm_cust_info(conn):
    print("2. Truncating and populating silver.crm_cust_info...")
    conn.sql("TRUNCATE TABLE silver.crm_cust_info;")
    conn.sql("""
             INSERT INTO silver.crm_cust_info (cst_id,
                                               cst_key,
                                               cst_firstname,
                                               cst_lastname,
                                               cst_marital_status,
                                               cst_gndr,
                                               cst_create_date)
             SELECT cst_id,
                    cst_key,
                    cst_firstname,
                    cst_lastname,
                    cst_marital_status,
                    cst_gndr,
                    cst_create_date
             FROM (SELECT cst_id::INT AS cst_id, TRIM(cst_key) AS cst_key,
                          TRIM(cst_firstname) AS cst_firstname,
                          TRIM(cst_lastname)  AS cst_lastname,
                          CASE
                              WHEN UPPER(TRIM(cst_marital_status)) = 'S' THEN 'Single'
                              WHEN UPPER(TRIM(cst_marital_status)) = 'M' THEN 'Married'
                              ELSE 'n/a'
                              END             AS cst_marital_status,
                          CASE
                              WHEN UPPER(TRIM(cst_gndr)) = 'F' THEN 'Female'
                              WHEN UPPER(TRIM(cst_gndr)) = 'M' THEN 'Male'
                              ELSE 'n/a'
                              END             AS cst_gndr,
                          cst_create_date::DATE AS cst_create_date, ROW_NUMBER() OVER (
                    PARTITION BY cst_id 
                    ORDER BY cst_create_date DESC
                ) AS last_flag
                   FROM bronze.crm_cust_info
                   WHERE cst_id IS NOT NULL) sub
             WHERE last_flag = 1;
             """)

def load_crm_prd_info(conn):
    print("3. Truncating and populating silver.crm_prd_info...")
    conn.sql("TRUNCATE TABLE silver.crm_prd_info;")
    conn.sql(""" 
            INSERT INTO silver.crm_prd_info (prd_id,
                                               cat_id,
                                               prd_key,
                                               prd_nm,
                                               prd_cost,
                                               prd_line,
                                               prd_start_dt,
                                               prd_end_dt
            )
            SELECT prd_id::INT AS prd_id,
            REPLACE(SUBSTRING(prd_key, 1, 5), '-', '_') AS cat_id, -- Extract category ID
			SUBSTRING(prd_key, 7, LEN(prd_key)) AS prd_key,        -- Extract product key
			prd_nm,
			COALESCE(prd_cost, 0)::INT AS prd_cost,
			CASE 
				WHEN UPPER(TRIM(prd_line)) = 'M' THEN 'Mountain'
				WHEN UPPER(TRIM(prd_line)) = 'R' THEN 'Road'
				WHEN UPPER(TRIM(prd_line)) = 'S' THEN 'Other Sales'
				WHEN UPPER(TRIM(prd_line)) = 'T' THEN 'Touring'
				ELSE 'n/a'
			END AS prd_line, -- Map product line codes to descriptive values
			prd_start_dt::DATE AS prd_start_dt,
			(LEAD(prd_start_dt::DATE) OVER (
                PARTITION BY SUBSTRING(prd_key, 7) 
                ORDER BY prd_start_dt::DATE
            ) - INTERVAL 1 DAY)::DATE AS prd_end_dt
             FROM bronze.crm_prd_info;
    
    """)

def load_crm_sales_details(conn):
    print("4. Truncating and populating silver.crm_sales_details...")
    conn.sql("TRUNCATE TABLE silver.crm_sales_details;")
    conn.sql(""" INSERT INTO silver.crm_sales_details (sls_ord_num,
                                                       sls_prd_key,
                                                       sls_cust_id,
                                                       sls_order_dt,
                                                       sls_ship_dt,
                                                       sls_due_dt,
                                                       sls_sales,
                                                       sls_quantity,
                                                       sls_price
    )
    SELECT sls_ord_num,
           sls_prd_key,
           sls_cust_id::INT AS sls_cust_id,
           CASE 
				WHEN sls_order_dt = 0 OR LENGTH(sls_order_dt::VARCHAR) != 8 THEN NULL
				ELSE strptime(sls_order_dt::VARCHAR, '%Y%m%d')::DATE
			END AS sls_order_dt,
			CASE 
				WHEN sls_ship_dt = 0 OR LENGTH(sls_ship_dt::VARCHAR) != 8 THEN NULL
				ELSE strptime(sls_ship_dt::VARCHAR, '%Y%m%d')::DATE
			END AS sls_ship_dt,
			CASE 
				WHEN sls_due_dt = 0 OR LENGTH(sls_due_dt::VARCHAR) != 8 THEN NULL
				ELSE strptime(sls_due_dt::VARCHAR, '%Y%m%d')::DATE
			END AS sls_due_dt,
			CASE 
				WHEN sls_sales IS NULL OR sls_sales <= 0 OR sls_sales != sls_quantity * ABS(sls_price) 
					THEN sls_quantity * ABS(sls_price)
				ELSE sls_sales
			END AS sls_sales, -- Recalculate sales if original value is missing or incorrect
			sls_quantity,
			CASE 
                WHEN sls_price IS NULL OR sls_price <= 0 
                    THEN sls_sales / NULLIF(sls_quantity, 0)
                ELSE ABS(sls_price)
            END AS sls_price
        FROM bronze.crm_sales_details;
    """)

def load_erp_loc_a101(conn):
    print("5. Truncating and populating silver.erp_loc_a101...")
    conn.sql("TRUNCATE TABLE silver.erp_loc_a101;")
    conn.sql("""
    INSERT INTO silver.erp_loc_a101 (cid, cntry)
    SELECT 
        REPLACE(cid, '-', '') AS cid,
        CASE
				WHEN TRIM(cntry) = 'DE' THEN 'Germany'
				WHEN TRIM(cntry) IN ('US', 'USA') THEN 'United States'
				WHEN TRIM(cntry) = '' OR cntry IS NULL THEN 'n/a'
				ELSE TRIM(cntry)
			END AS cntry -- Normalize and Handle missing or blank country codes
    FROM bronze.erp_loc_a101;
    """)

def load_erp_cust_az12(conn):
    print("6. Truncating and populating silver.cust_az12...")
    conn.sql("TRUNCATE TABLE silver.erp_cust_az12;")
    conn.sql("""
    INSERT INTO silver.erp_cust_az12 (cid, bdate, gen)
    SELECT
        CASE
				WHEN cid LIKE 'NAS%' THEN SUBSTRING(cid, 4, LENGTH(cid)) -- Remove 'NAS' prefix if present
				ELSE cid
			END AS cid, 
			CASE
				WHEN bdate > CURRENT_DATE() THEN NULL
				ELSE bdate
			END AS bdate, -- Set future birthdates to NULL
			CASE
				WHEN UPPER(TRIM(gen)) IN ('F', 'FEMALE') THEN 'Female'
				WHEN UPPER(TRIM(gen)) IN ('M', 'MALE') THEN 'Male'
				ELSE 'n/a'
			END AS gen -- Normalize gender values and handle unknown cases
		FROM bronze.erp_cust_az12;
    """)

def load_erp_px_cat_g1v2(conn):
    print("7. Truncating and populating silver.prp_px_cat_g1v2...")
    conn.sql("TRUNCATE TABLE silver.erp_px_cat_g1v2;")
    conn.sql("""
    INSERT INTO silver.erp_px_cat_g1v2 (id,
                                        cat, 
                                        subcat, 
                                        maintenance)
    SELECT
        id,
        cat, 
        subcat,
        maintenance
    FROM bronze.erp_px_cat_g1v2;
    """)

def main():
    with duckdb.connect(str(DB_PATH)) as conn:
        init_silver_tables(conn)
        print("Silver layer DDL executed successfully!")
        load_crm_cust_info(conn)
        print(" Populated silver.crm_cust_info without duplicates and cleaned data.")
        load_crm_prd_info(conn)
        print(" Populated silver.crm_prd_info with cleaned data.")
        load_crm_sales_details(conn)
        print(" Populated silver.crm_sales_details with cleaned data.")
        load_erp_loc_a101(conn)
        print(" Populated silver.erp_loc_a101 with cleaned data.")
        load_erp_cust_az12(conn)
        print(" Populated silver.erp_cust_az12 with cleaned data.")
        load_erp_px_cat_g1v2(conn)
        print(" Populated silver.erp_px_cat_g1v2 with cleaned data.")


if __name__ == "__main__":
    main()