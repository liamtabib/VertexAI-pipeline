# SummaryAI: ecommerce analytics with AI insights

This project is an end-to-end analytics pipeline for ecommerce data with AI-powered insights and conversational analytics. It also serves as educational purpose to learn how to build data pipelines with **Python**, **Dagster**, **dbt**, **Vertex AI**, and **GCP**. You can see the final result of the project in this live [dashboard](https://your-dashboard-url.com/).

![demo](./docs/demo_dashboard.gif)

## High level architecture
![High level architecture](./docs/architecture.png)

## Vertex-AI Data Slackbot
![Slackbot demo](./docs/demo_slackbot.png)

## Project Structure

```
├── pipeline/
│   ├── orchestration/
│   │   └── dagster_pipeline.py
│   ├── transform/ecommerce_metrics/
│   ├── export/
│   │   └── export_to_duckdb.py
│   └── gemini_summarizer/
│       ├── main.py
│       └── Dockerfile
├── dashboard/
├── services/
│   └── analytics_chat/
├── tests/
├── docs/
├── pyproject.toml
└── uv.lock
```

## Development Setup

### Requirements

- Python 3.12
- Google Cloud Project with enabled APIs:
  - BigQuery API
  - Vertex AI API
  - Cloud Run API
- Service account with appropriate permissions

### Environment Configuration

```bash
# Clone and install
git clone <repo-url>
cd SummaryAI
uv sync

# Configure credentials
cp .env.example .env
```

Required environment variables:
```bash
GCP_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
VERTEX_LOCATION=us-central1
VERTEX_MODEL=gemini-1.5-flash
BQ_DATASET=ecommerce_analytics

# Optional: Slack Integration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=analytics-alerts
```

## Pipeline Stages

The complete pipeline is orchestrated by Dagster in `pipeline/orchestration/dagster_pipeline.py`. For the full pipeline, use:

```bash
uv run dagster dev
```

### Pipeline Steps

**1. Data transformation** (`ecommerce_dbt_assets`)  
Processes BigQuery public ecommerce dataset using dbt models to create analytics-ready tables for MAU, retention, platform share, and funnel metrics.

**2. DuckDB export** (`export_to_duckdb`)  
Exports all dbt models from BigQuery to local DuckDB file for fast Evidence.dev dashboard queries.

**3. AI analysis** (`gemini_summary`)  
Triggers Cloud Run job that uses Vertex AI (Gemini) to analyze metrics and generate automated insights with structured facts.

**4. Summary sync** (`sync_summary`)  
Syncs AI-generated summaries from BigQuery to DuckDB making insights available to the dashboard.

**5. Dashboard build** (`evidence_dashboard`)  
Builds Evidence.dev dashboard with fresh data and AI insights, generating static site ready for deployment.

### Manual Execution

Individual components can also be run separately:

```bash
# Just dbt transformation
cd pipeline/transform/ecommerce_metrics && dbt build

# Launch dashboard locally  
cd dashboard && npm run dev
```

