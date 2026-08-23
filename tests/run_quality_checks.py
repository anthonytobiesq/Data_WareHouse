from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "DataWarehouse.duckdb"


def run_assertions(conn, tests):
    """Runs queries expected to return 0 rows. Fails if invalid records exist."""
    failed = 0
    for name, query in tests.items():
        res = conn.sql(query).fetchall()
        count = len(res)
        if count > 0:
            print(f"❌ FAILED: [{name}] — Found {count} invalid records!")
            failed += 1
        else:
            print(f" PASSED: [{name}]")
    return failed


def run_audits(conn, audits):
    """Runs inspection queries to display distinct values and verify standardization."""
    print("\n Inspecting Standardized Categorical Columns...")
    for name, query in audits.items():
        res = [row[0] for row in conn.sql(query).fetchall()]
        print(f" 🔍 AUDIT [{name}]: {res}")


def run_silver_checks(conn):
    print(" Running Complete Silver Layer Data Quality Checks...\n")

    silver_assertions = {
        # --- CRM CUST INFO ---
        "Silver CRM Cust Primary Key Uniqueness": """
                                                  SELECT cst_id, COUNT(*)
                                                  FROM silver.crm_cust_info
                                                  GROUP BY cst_id
                                                  HAVING COUNT(*) > 1
                                                      OR cst_id IS NULL;
                                                  """,
        "Silver CRM Cust Unwanted Spaces": """
                                           SELECT cst_key
                                           FROM silver.crm_cust_info
                                           WHERE cst_key != TRIM(cst_key);
                                           """,

        # --- CRM PRD INFO ---
        "Silver CRM Prd Primary Key Uniqueness": """
                                                 SELECT prd_id, COUNT(*)
                                                 FROM silver.crm_prd_info
                                                 GROUP BY prd_id
                                                 HAVING COUNT(*) > 1
                                                     OR prd_id IS NULL;
                                                 """,
        "Silver CRM Prd Unwanted Spaces": """
                                          SELECT prd_nm
                                          FROM silver.crm_prd_info
                                          WHERE prd_nm != TRIM(prd_nm);
                                          """,
        "Silver CRM Prd Negative or NULL Cost": """
                                                SELECT prd_cost
                                                FROM silver.crm_prd_info
                                                WHERE prd_cost < 0
                                                   OR prd_cost IS NULL;
                                                """,
        "Silver CRM Prd Invalid Dates": """
                                        SELECT *
                                        FROM silver.crm_prd_info
                                        WHERE prd_end_dt < prd_start_dt;
                                        """,

        # --- CRM SALES DETAILS ---
        "Silver CRM Sales Date Ordering": """
                                          SELECT *
                                          FROM silver.crm_sales_details
                                          WHERE sls_order_dt > sls_ship_dt
                                             OR sls_order_dt > sls_due_dt;
                                          """,
        "Silver CRM Sales Price Calculations": """
                                               SELECT sls_sales, sls_quantity, sls_price
                                               FROM silver.crm_sales_details
                                               WHERE sls_sales != sls_quantity * sls_price 
               OR sls_sales IS NULL OR sls_quantity IS NULL OR sls_price IS NULL 
               OR sls_sales <= 0 OR sls_quantity <= 0 OR sls_price <= 0;
                                               """,

        # --- ERP TABLES ---
        "Silver ERP Cust Out-of-Range Birthdates": """
                                                   SELECT bdate
                                                   FROM silver.erp_cust_az12
                                                   WHERE bdate < '1924-01-01'
                                                      OR bdate > CURRENT_DATE;
                                                   """,
        "Silver ERP Cat Unwanted Spaces": """
                                          SELECT *
                                          FROM silver.erp_px_cat_g1v2
                                          WHERE cat != TRIM(cat) OR subcat != TRIM(subcat) OR maintenance != TRIM(maintenance);
                                          """
    }

    # Distinct checks to verify mapping logic output
    silver_audits = {
        "CRM Customer Marital Status": "SELECT DISTINCT cst_marital_status FROM silver.crm_cust_info;",
        "CRM Customer Gender": "SELECT DISTINCT cst_gndr FROM silver.crm_cust_info;",
        "CRM Product Line": "SELECT DISTINCT prd_line FROM silver.crm_prd_info;",
        "ERP Customer Gender": "SELECT DISTINCT gen FROM silver.erp_cust_az12;",
        "ERP Location Countries": "SELECT DISTINCT cntry FROM silver.erp_loc_a101 ORDER BY cntry;",
        "ERP Maintenance Status": "SELECT DISTINCT maintenance FROM silver.erp_px_cat_g1v2;"
    }

    failed_count = run_assertions(conn, silver_assertions)
    run_audits(conn, silver_audits)

    if failed_count > 0:
        raise ValueError(f"\nPipeline halted! {failed_count} Silver quality check(s) failed.")
    else:
        print("\n All Silver Quality Checks & Audits Completed Successfully!")


def run_gold_checks(conn):
    print("\n Running Gold Layer Data Quality Checks...\n")

    gold_assertions = {
        "Gold Dim Customers Key Uniqueness": """
                                             SELECT customer_key, COUNT(*)
                                             FROM gold.dim_customers
                                             GROUP BY customer_key
                                             HAVING COUNT(*) > 1;
                                             """,
        "Gold Dim Products Key Uniqueness": """
                                            SELECT product_key, COUNT(*)
                                            FROM gold.dim_products
                                            GROUP BY product_key
                                            HAVING COUNT(*) > 1;
                                            """,
        "Gold Fact Sales Referential Integrity": """
                                                 SELECT f.sls_ord_num
                                                 FROM gold.fact_sales f
                                                          LEFT JOIN gold.dim_customers c ON c.customer_key = f.customer_key
                                                          LEFT JOIN gold.dim_products p ON p.product_key = f.product_key
                                                 WHERE p.product_key IS NULL
                                                    OR c.customer_key IS NULL;
                                                 """
    }

    failed_count = run_assertions(conn, gold_assertions)
    if failed_count > 0:
        raise ValueError(f"Gold quality checks failed with {failed_count} errors.")


def main():
    with duckdb.connect(str(DB_PATH)) as conn:
        run_silver_checks(conn)
        # Uncomment after creating Gold layer tables:
        #run_gold_checks(conn)


if __name__ == "__main__":
    main()