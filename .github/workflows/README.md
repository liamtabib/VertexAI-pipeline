# GitHub Actions Configuration

## Repository Secrets Required

Configure the following secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

### Required Secrets

- **`GCP_SECRETS`** - Service account JSON with permissions for:
  - BigQuery Admin
  - Vertex AI User  
  - Cloud Run Invoker
  - Storage Admin (if using Cloud Storage)

- **`GCP_PROJECT_ID`** - Your Google Cloud Project ID (e.g., `pipeline-466508`)

- **`VERTEX_LOCATION`** - Vertex AI region (e.g., `us-central1`)

- **`VERTEX_MODEL`** - Vertex AI model name (e.g., `gemini-1.5-flash`)

### Optional Secrets

- **`SLACK_BOT_TOKEN`** - Slack bot token for notifications (if using Slack integration)

- **`SLACK_CHANNEL`** - Slack channel ID for notifications (if using Slack integration)

## Workflow Details

- **Schedule**: Runs weekly on Mondays at 6 AM UTC
- **Manual trigger**: Available via workflow_dispatch
- **Pipeline**: `ecommerce_analytics_pipeline` job from `pipeline/orchestration/dagster_pipeline.py`
- **Dashboard data**: Automatically commits updated `dashboard_data.duckdb` to repository
- **Failure handling**: Creates GitHub issues for pipeline failures with detailed logs

## Service Account Permissions

Your GCP service account needs the following IAM roles:

```
roles/bigquery.admin
roles/aiplatform.user
roles/run.invoker
roles/storage.admin (if using Cloud Storage)
```

## Pipeline Assets Executed

1. `ecommerce_dbt_assets` - dbt transformation on BigQuery ecommerce dataset
2. `export_to_duckdb` - Export dbt models to local DuckDB
3. `gemini_summary` - Trigger Cloud Run job for AI analysis  
4. `sync_summary` - Sync AI summaries to DuckDB
5. `evidence_dashboard` - Build Evidence.dev dashboard