import os
import subprocess
from pathlib import Path
import time

from dagster import (
    asset, 
    AssetExecutionContext,
    Definitions,
    define_asset_job
)
from dagster_dbt import DbtCliResource, dbt_assets

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Cloud Run and DuckDB sync functions
import requests
from google.auth import default
from google.auth.transport.requests import Request
import duckdb

def _access_token(scope="https://www.googleapis.com/auth/cloud-platform"):
    creds, _ = default(scopes=[scope]); creds.refresh(Request()); return creds.token

def trigger_cloud_run_job(project, region, job_name, run_id=None):
    """Trigger Cloud Run Job with retry logic and error handling"""
    import time
    
    # Use Cloud Run Jobs API v2 endpoint
    url = f"https://run.googleapis.com/v2/projects/{project}/locations/{region}/jobs/{job_name}:run"
    
    # Read prompt content from repository to ensure latest version is used
    prompt_path = Path(__file__).parent.parent / "gemini_summarizer" / "prompt.txt"
    prompt_content = prompt_path.read_text(encoding="utf-8")
    
    # Prepare environment variables for container
    env_vars = [{"name": "PROMPT_CONTENT", "value": prompt_content}]
    if run_id:
        env_vars.append({"name": "RUN_ID", "value": run_id})
    
    body = {"overrides": {"containerOverrides": [{"env": env_vars}]}} if env_vars else {}
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.post(
                url, 
                json=body or {}, 
                headers={"Authorization": f"Bearer {_access_token()}"}, 
                timeout=120
            )
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed to trigger Cloud Run Job after {max_retries} attempts: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff

def sync_summary_to_duckdb(project, dataset, duckdb_path, run_id=None):
    """Sync summary from BigQuery to DuckDB with error handling"""
    try:
        from google.cloud import bigquery
        bq = bigquery.Client(project=project)
        
        if run_id:
            sql = f"SELECT * FROM `{project}.{dataset}.summaries` WHERE run_id=@r ORDER BY run_ts DESC LIMIT 1"
            job_cfg = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("r","STRING", run_id)])
        else:
            sql = f"SELECT * FROM `{project}.{dataset}.summaries` ORDER BY run_ts DESC LIMIT 1"
            job_cfg = None
            
        rows = list(bq.query(sql, job_config=job_cfg).result())
        if not rows: 
            raise Exception(f"No summary found in BigQuery for run_id: {run_id}")
            
        r = dict(rows[0])
        
        # Ensure DuckDB file directory exists
        import os
        os.makedirs(os.path.dirname(duckdb_path), exist_ok=True)
        
        con = duckdb.connect(duckdb_path)
        try:
            con.execute("""CREATE TABLE IF NOT EXISTS summaries(
                run_id VARCHAR, run_ts TIMESTAMP, data_end_date DATE, text TEXT, facts_json JSON,
                sent_slack_ts VARCHAR, sent_email_id VARCHAR)""")
            con.execute("DELETE FROM summaries WHERE run_id = ?", [r["run_id"]])
            con.execute("INSERT INTO summaries VALUES (?,?,?,?,?,?,?)",
                        [r["run_id"], r["run_ts"], r["data_end_date"], r["text"], r["facts_json"],
                         r["sent_slack_ts"], r["sent_email_id"]])
        finally:
            con.close()
            
    except Exception as e:
        raise Exception(f"Failed to sync summary to DuckDB: {e}")




@dbt_assets(
    manifest=Path(__file__).parent.parent / "transform" / "ecommerce_metrics" / "target" / "manifest.json",
)
def ecommerce_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    """dbt assets for transforming ecommerce data from BigQuery public dataset"""
    try:
        yield from dbt.cli(["build"], context=context).stream()
    except Exception as e:
        context.log.error(f"dbt build failed: {str(e)}")
        raise


@asset(
    description="Export all dbt models from BigQuery to DuckDB for Evidence dashboard",
    deps=[ecommerce_dbt_assets],
    group_name="export"
)
def export_to_duckdb(context: AssetExecutionContext) -> str:
    """Export dbt models from BigQuery to DuckDB for Evidence"""
    try:
        script_path = Path(__file__).parent.parent / "export" / "export_to_duckdb.py"
        
        context.log.info("Running export script to DuckDB...")
        result = subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("Export script output:")
        context.log.info(result.stdout)
        
        if result.stderr:
            context.log.warning(f"Export script warnings: {result.stderr}")
        
        duckdb_path = Path(__file__).parent.parent.parent / "dashboard" / "sources" / "dashboard_data" / "dashboard_data.duckdb"
        context.log.info(f"Data exported to DuckDB at {duckdb_path}")
        
        return str(duckdb_path)
        
    except subprocess.CalledProcessError as e:
        context.log.error(f"Export script failed with exit code {e.returncode}")
        context.log.error(f"stdout: {e.stdout}")
        context.log.error(f"stderr: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Failed to export to DuckDB: {str(e)}")
        raise


@asset(
    description="Build Evidence dashboard",
    deps=[export_to_duckdb],
    group_name="dashboard"
)
def evidence_dashboard(context: AssetExecutionContext, export_to_duckdb: str) -> str:
    """Build Evidence dashboard with fresh data"""
    try:
        dashboard_dir = Path(__file__).parent.parent.parent / "dashboard"
        
        context.log.info("Building Evidence dashboard...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=dashboard_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("Evidence build output:")
        context.log.info(result.stdout)
        
        if result.stderr:
            context.log.warning(f"Evidence build warnings: {result.stderr}")
        
        context.log.info(f"Evidence dashboard built successfully using data from {export_to_duckdb}")
        return "dashboard_built"
        
    except subprocess.CalledProcessError as e:
        context.log.error(f"Evidence build failed with exit code {e.returncode}")
        context.log.error(f"stdout: {e.stdout}")
        context.log.error(f"stderr: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Failed to build Evidence dashboard: {str(e)}")
        raise


@asset(
    description="Generate AI summary using Cloud Run Job",
    deps=[export_to_duckdb],
    group_name="summary"
)
def gemini_summary(context: AssetExecutionContext) -> str:
    """Trigger Cloud Run Job for Gemini summarizer"""
    try:
        project = os.getenv("GCP_PROJECT", "pipeline-466508")
        region = "us-central1"
        job_name = "gemini-summarizer"
        run_id = time.strftime("%Y-%m-%d")
        
        context.log.info(f"Triggering Cloud Run Job: {job_name} with run_id: {run_id}")
        
        # Trigger Cloud Run Job
        trigger_cloud_run_job(project, region, job_name, run_id)
        
        context.log.info("✓ Cloud Run Job triggered successfully")
        context.log.info(f"Monitor execution at: https://console.cloud.google.com/run/jobs/details/{region}/{job_name}?project={project}")
        
        # Wait for job completion and verify with enhanced monitoring
        import time as time_module
        max_wait = 600  # 10 minutes timeout
        wait_interval = 15
        elapsed = 0
        
        context.log.info("Waiting for Cloud Run Job to complete...")
        while elapsed < max_wait:
            time_module.sleep(wait_interval)
            elapsed += wait_interval
            
            # Check if summary was created in BigQuery
            try:
                from google.cloud import bigquery
                bq = bigquery.Client(project=project)
                check_sql = f"SELECT COUNT(*) as count FROM `{project}.ecommerce_analytics.summaries` WHERE run_id = @run_id"
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ScalarQueryParameter("run_id", "STRING", run_id)]
                )
                result = list(bq.query(check_sql, job_config=job_config).result())
                if result[0]["count"] > 0:
                    context.log.info(f"✓ Summary found in BigQuery for run_id: {run_id}")
                    return run_id
                else:
                    context.log.info(f"Waiting... ({elapsed}s/{max_wait}s)")
            except Exception as check_error:
                context.log.warning(f"Error checking BigQuery: {check_error}")
                
            # Additional monitoring: check Cloud Run execution status
            try:
                import subprocess
                result = subprocess.run([
                    "gcloud", "run", "jobs", "executions", "list",
                    f"--job={job_name}",
                    f"--region={region}",
                    "--limit=1",
                    "--format=value(name,status)"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and result.stdout.strip():
                    execution_name, status = result.stdout.strip().split('\t')
                    context.log.info(f"Cloud Run execution {execution_name}: {status}")
                    if status == "FAILED":
                        raise Exception(f"Cloud Run Job failed: {execution_name}")
            except subprocess.TimeoutExpired:
                context.log.warning("Timeout checking Cloud Run status")
            except Exception as monitor_error:
                context.log.warning(f"Error monitoring Cloud Run: {monitor_error}")
        
        # If we reach here, job may have failed or timed out
        raise Exception(f"Cloud Run Job did not complete within {max_wait}s - check Cloud Console for details")
        
    except Exception as e:
        context.log.error(f"Failed to trigger Cloud Run Job: {str(e)}")
        raise


@asset(
    description="Sync AI summary from BigQuery to DuckDB",
    deps=[gemini_summary],
    group_name="summary"
)
def sync_summary(context: AssetExecutionContext, gemini_summary: str) -> str:
    """Sync latest summary from BigQuery to DuckDB for Evidence"""
    try:
        project = os.getenv("GCP_PROJECT")
        dataset = "ecommerce_analytics"
        duckdb_path = Path(__file__).parent.parent.parent / "dashboard" / "sources" / "dashboard_data" / "dashboard_data.duckdb"
        
        context.log.info(f"Syncing summary with run_id: {gemini_summary} to DuckDB")
        sync_summary_to_duckdb(project, dataset, str(duckdb_path), gemini_summary)
        
        context.log.info("✓ Summary synced to DuckDB successfully")
        return str(duckdb_path)
        
    except Exception as e:
        context.log.error(f"Failed to sync summary to DuckDB: {str(e)}")
        raise


# Define the main pipeline job
ecommerce_pipeline_job = define_asset_job(
    name="ecommerce_analytics_pipeline",
    selection=[ecommerce_dbt_assets, export_to_duckdb, gemini_summary, sync_summary, evidence_dashboard],
    description="Complete ecommerce analytics pipeline: dbt models → DuckDB export → AI summary → Evidence dashboard",
)


# Define Dagster resources and assets
defs = Definitions(
    assets=[ecommerce_dbt_assets, export_to_duckdb, gemini_summary, sync_summary, evidence_dashboard],
    jobs=[ecommerce_pipeline_job],
    resources={
        "dbt": DbtCliResource(
            project_dir=Path(__file__).parent.parent / "transform" / "ecommerce_metrics",
            profiles_dir=Path(__file__).parent.parent / "transform" / "ecommerce_metrics",
        ),
    }
)