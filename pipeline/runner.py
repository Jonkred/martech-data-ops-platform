import os
import json
import time
import psycopg2
import subprocess
import requests

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "data_engineer")
DB_PASS = os.getenv("DB_PASS", "devpassword")
DB_NAME = os.getenv("DB_NAME", "analytics_dw")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME
    )

def init_raw_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.raw_stream_events (
            id VARCHAR PRIMARY KEY,
            anonymous_id VARCHAR,
            user_id VARCHAR,
            event_type VARCHAR,
            properties JSON,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS public.pipeline_metrics (
            id SERIAL PRIMARY KEY,
            pipeline_name VARCHAR,
            records_processed INT,
            duration_ms FLOAT,
            status VARCHAR,
            error_details TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def generate_mock_events():
    conn = get_connection()
    cur = conn.cursor()
    # Simula eventos crus de tracking mobile/web
    cur.execute("""
        INSERT INTO public.raw_stream_events (id, anonymous_id, user_id, event_type, properties)
        VALUES 
            (gen_random_uuid()::varchar, 'anon_812', NULL, 'product_viewed', '{"item": "headphone"}'),
            (gen_random_uuid()::varchar, 'anon_812', 'usr_99', 'order_completed', '{"item": "headphone", "revenue": 450.00}'),
            (gen_random_uuid()::varchar, 'anon_404', 'usr_102', 'order_completed', '{"item": "laptop", "revenue": 1800.00}')
        ON CONFLICT (id) DO NOTHING;
    """)
    conn.commit()
    cur.close()
    conn.close()
def run_dbt_transformations():
    start_time = time.time()
    result = subprocess.run(
        ["dbt", "build", "--project-dir", "dbt_project", "--profiles-dir", "dbt_project"],
        capture_output=True,
        text=True
    )
    duration = (time.time() - start_time) * 1000
    status = "SUCCESS" if result.returncode == 0 else "FAILED"
    
    print("[*] dbt output:")
    print(result.stdout)
    if result.stderr:
        print("[!] dbt errors:\n", result.stderr)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO public.pipeline_metrics (pipeline_name, records_processed, duration_ms, status, error_details)
        VALUES (%s, %s, %s, %s, %s)
    """, ("dbt_medallion_build", 3, duration, status, result.stderr if status == "FAILED" else None))
    conn.commit()
    cur.close()
    conn.close()
    return result.returncode == 0

def reverse_etl_to_martech():
    """Simula envio de audiências calculadas para Braze/Segment."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT resolved_customer_id, audience_segment, total_revenue_ltv FROM gold.mart_customer_rfm WHERE audience_segment = 'VIP';")
    vip_users = cur.fetchall()
    
    payload = [
        {"external_id": row[0], "attributes": {"segment": row[1], "ltv": float(row[2])}}
        for row in vip_users
    ]
    
    # Mocking endpoint sync (200 OK)
    print(f"[*] Reverse ETL Synced {len(payload)} VIP users to MarTech CDP payload:")
    print(json.dumps(payload, indent=2))
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    init_raw_tables()
    generate_mock_events()
    success = run_dbt_transformations()
    if success:
        reverse_etl_to_martech()