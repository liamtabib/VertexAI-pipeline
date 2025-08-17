import os
import subprocess
from pathlib import Path

from dagster import (
    asset, 
    AssetExecutionContext,
    Config,
    Definitions,
    define_asset_job
)
from dagster_dbt import DbtCliResource, dbt_assets

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class EcommerceConfig(Config):
    gcp_project: str = os.getenv("GCP_PROJECT", "your-project-id")
    bq_dataset: str = "ecommerce_analytics"


@dbt_assets(
    manifest=Path(__file__).parent / "transform" / "ecommerce_metrics" / "target" / "manifest.json",
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
        script_path = Path(__file__).parent / "export_to_duckdb.py"
        
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
        
        duckdb_path = Path(__file__).parent / "dashboard" / "sources" / "dashboard_data" / "dashboard_data.duckdb"
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
        dashboard_dir = Path(__file__).parent / "dashboard"
        
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


# Define the main pipeline job
ecommerce_pipeline_job = define_asset_job(
    name="ecommerce_analytics_pipeline",
    selection=[ecommerce_dbt_assets, export_to_duckdb, evidence_dashboard],
    description="Complete ecommerce analytics pipeline: dbt models → DuckDB export → Evidence dashboard",
)


# Define Dagster resources and assets
defs = Definitions(
    assets=[ecommerce_dbt_assets, export_to_duckdb, evidence_dashboard],
    jobs=[ecommerce_pipeline_job],
    resources={
        "dbt": DbtCliResource(
            project_dir=Path(__file__).parent / "transform" / "ecommerce_metrics",
            profiles_dir=Path(__file__).parent / "transform" / "ecommerce_metrics",
        ),
    }
)