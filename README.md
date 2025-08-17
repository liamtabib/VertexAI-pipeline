# Ecommerce Analytics Dashboard

This project provides a comprehensive analytics pipeline for ecommerce data using the BigQuery public dataset `bigquery-public-data.thelook_ecommerce`. It demonstrates modern data engineering practices with **dbt**, **DuckDB**, **Evidence.dev**, and **Dagster**.

## Architecture

```
BigQuery Public Dataset → dbt Models → DuckDB Export → Evidence.dev Dashboard
                     ↑
                 Dagster Orchestration
```

The pipeline:
1. **Sources**: Uses the BigQuery public ecommerce dataset
2. **Transform**: dbt models create analytics-ready tables  
3. **Export**: Exports transformed data to local DuckDB for fast analytics
4. **Visualize**: Evidence.dev renders interactive dashboard from DuckDB
5. **Orchestrate**: Dagster manages the end-to-end pipeline

## Project Structure

```
├── transform/ecommerce_metrics/     # dbt project for data modeling
│   ├── models/                      # SQL models for metrics
│   ├── dbt_project.yml
│   └── profiles.yml
├── dashboard/                       # Evidence.dev dashboard
│   ├── pages/index.md              # Main dashboard page
│   └── sources/dashboard_data/     # SQL queries and connection
├── export_to_duckdb.py             # BigQuery to DuckDB export script
├── dagster_pipeline.py             # Orchestration pipeline
├── pyproject.toml                  # Python dependencies
└── metrics_and_visuals.txt         # Metrics specification
```

## Dashboard Features

The dashboard provides comprehensive ecommerce analytics:

### Key Visualizations
- **Monthly Active Users (MAU)**: Trend of user activity over time
- **Cohort Retention**: User retention analysis by registration cohort
- **Geographic Distribution**: World map of users by country
- **Platform Analysis**: User distribution across Android, iOS, Desktop, Web
- **Shopping Funnel**: 5-step conversion funnel analysis

### Data Quality
- Monthly metrics exclude the current (potentially partial) month
- Funnel analysis uses the latest complete month
- Retention analysis focuses on the 5 most recent cohorts
- All data is sourced from the reliable BigQuery public dataset

## Development Setup

### Requirements

- Python 3.12
- Google Cloud Project with BigQuery API enabled
- Service account with BigQuery read permissions
- Node.js (for Evidence.dev dashboard)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd ecommerce-analytics

# Install Python dependencies
uv sync

# Install Evidence.dev dependencies
cd dashboard && npm install
```

### Environment Configuration

Create a `.env` file with required variables:

```bash
GCP_PROJECT=your-google-cloud-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

### dbt Configuration

Update `transform/ecommerce_metrics/profiles.yml` with your GCP project details.

## Running the Pipeline

### Complete Pipeline

Launch the full orchestrated pipeline with Dagster:

```bash
uv run dagster dev
```

Navigate to `http://localhost:3000` to view the Dagster UI and run the `ecommerce_analytics_pipeline` job.

### Individual Components

Run components separately for development:

```bash
# dbt models only
cd transform/ecommerce_metrics
dbt build

# Export to DuckDB only
python export_to_duckdb.py

# Evidence dashboard only
cd dashboard
npm run dev
```

## Pipeline Stages

1. **dbt Transformation** (`ecommerce_dbt_assets`)
   - Processes BigQuery public dataset
   - Creates analytics-ready models (MAU, retention, platform share, etc.)
   - Materializes tables in your BigQuery project

2. **DuckDB Export** (`export_to_duckdb`)
   - Exports all dbt models from BigQuery to local DuckDB
   - Optimizes for fast Evidence.dev query performance

3. **Dashboard Build** (`evidence_dashboard`)
   - Builds Evidence.dev dashboard with fresh data
   - Generates static site ready for deployment

## Dashboard Metrics

### Monthly Active Users (MAU)
- Counts distinct users with activity per calendar month
- Excludes current month to ensure complete data

### Cohort Retention
- Tracks user retention by registration month
- Shows retention rates for the 5 most recent cohorts
- Filters out small cohorts (<50 users) for statistical significance

### Geographic Analysis
- User distribution by country
- Excludes null country values
- Visualized on world map

### Platform Distribution
- Classifies users by dominant platform based on latest activity
- Categories: Android, iOS, Desktop, Web
- Based on browser string analysis

### Shopping Funnel
- 5-step conversion analysis: home → department → product → cart → purchase
- Uses latest complete month data
- Session-based funnel logic

## Data Source

All data comes from the BigQuery public dataset `bigquery-public-data.thelook_ecommerce`, which includes:
- **events**: User behavior events with timestamps and session info
- **users**: User registration and profile data

This is a synthetic but realistic ecommerce dataset perfect for analytics demonstrations.

## Contributing

1. Fork the repository
2. Create feature branch
3. Add your improvements
4. Test the complete pipeline
5. Submit pull request

## License

MIT License - see LICENSE file for details.