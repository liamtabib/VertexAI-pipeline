#!/usr/bin/env python3
"""
Export dbt models from BigQuery to DuckDB for Evidence.dev dashboard
"""

import os
import duckdb
from google.cloud import bigquery
from loguru import logger
import pandas as pd
from pathlib import Path


def export_table_to_duckdb(bq_client, table_name: str, project_id: str, dataset_id: str, duckdb_conn):
    """Export a single table from BigQuery to DuckDB"""
    try:
        query = f"""
        SELECT *
        FROM `{project_id}.{dataset_id}.{table_name}`
        """
        
        logger.info(f"Querying {table_name} from BigQuery...")
        df = bq_client.query(query).to_dataframe()
        
        # Convert BigQuery date types to strings for DuckDB compatibility
        for col in df.columns:
            if df[col].dtype == 'dbdate':
                df[col] = df[col].astype(str)
            elif 'datetime' in str(df[col].dtype).lower():
                df[col] = df[col].astype(str)
        
        logger.info(f"Writing {len(df)} rows to DuckDB table {table_name}")
        duckdb_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        duckdb_conn.register(f"{table_name}_df", df)
        duckdb_conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {table_name}_df")
        duckdb_conn.unregister(f"{table_name}_df")
        
        logger.info(f"✓ Successfully exported {table_name}")
        
    except Exception as e:
        logger.error(f"Failed to export {table_name}: {e}")
        raise


def main():
    # Configuration
    project_id = os.getenv('GCP_PROJECT')
    dataset_id = 'ecommerce_analytics'
    duckdb_path = Path(__file__).parent.parent.parent / 'dashboard' / 'sources' / 'dashboard_data' / 'dashboard_data.duckdb'
    
    # Tables to export (matching our dbt models)
    tables = [
        'mau',
        'retention', 
        'users_by_country',
        'platform_share',
        'funnel',
        'data_end_date',
        'country_trends',
        'kpi_metrics'
    ]
    
    if not project_id:
        raise ValueError("GCP_PROJECT environment variable not set")
    
    # Ensure DuckDB directory exists
    duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize clients
    logger.info("Initializing BigQuery client...")
    bq_client = bigquery.Client(project=project_id)
    
    logger.info(f"Connecting to DuckDB at {duckdb_path}")
    duckdb_conn = duckdb.connect(str(duckdb_path))
    
    try:
        # Export each table
        for table in tables:
            export_table_to_duckdb(bq_client, table, project_id, dataset_id, duckdb_conn)
        
        logger.info("✓ All tables exported successfully")
        
        # Show summary
        logger.info("DuckDB tables summary:")
        tables_info = duckdb_conn.execute("SHOW TABLES").fetchall()
        for table_info in tables_info:
            table_name = table_info[0]
            count = duckdb_conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            logger.info(f"  {table_name}: {count:,} rows")
            
    finally:
        duckdb_conn.close()


if __name__ == "__main__":
    main()