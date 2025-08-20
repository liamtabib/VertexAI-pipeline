# AI-Powered Ecommerce Analytics Dashboard

This project provides a comprehensive analytics pipeline for ecommerce data using the BigQuery public dataset `bigquery-public-data.thelook_ecommerce`. It demonstrates modern data engineering practices with **dbt**, **DuckDB**, **Evidence.dev**, **Dagster**, and **Vertex AI** for automated insights and notifications.


![demo](./docs/demo_dashboard.gif)

## High level architecture
![High level architecture](./docs/architecture.png)


## Slackbot demo
![Slackbot demo](./docs/demo_slackbot.png)


## Architecture

```
BigQuery Public Dataset → dbt Models → DuckDB Export → Evidence.dev Dashboard
                     ↑                       ↑              ↑
                 Dagster Orchestration → AI Analysis → Slack Notifications
                                         (Vertex AI)
```

The enhanced pipeline:
1. **Sources**: Uses the BigQuery public ecommerce dataset
2. **Transform**: dbt models create analytics-ready tables in BigQuery
3. **Export**: Exports transformed data to local DuckDB for fast analytics
4. **AI Analysis**: Vertex AI (Gemini) generates automated insights and summaries
5. **Sync**: AI summaries stored in BigQuery and synced to DuckDB
6. **Visualize**: Evidence.dev renders interactive dashboard with AI insights
7. **Notify**: Optional Slack bot provides conversational analytics interface
8. **Orchestrate**: Dagster manages the complete end-to-end pipeline

## Project Structure

```
├── pipeline/                        # Data pipeline components
│   ├── orchestration/
│   │   └── dagster_pipeline.py     # Main Dagster orchestration
│   ├── transform/ecommerce_metrics/  # dbt project for data modeling
│   │   ├── models/                  # SQL models for metrics
│   │   ├── dbt_project.yml
│   │   └── profiles.yml
│   ├── export/
│   │   └── export_to_duckdb.py     # BigQuery to DuckDB export script
│   └── gemini_summarizer/           # AI analysis service
│       ├── main.py                  # Vertex AI Gemini integration
│       ├── prompt.txt               # AI prompt template
│       └── Dockerfile               # Container for Cloud Run
├── dashboard/                       # Evidence.dev dashboard
│   ├── pages/index.md              # Main dashboard page with AI insights
│   └── sources/dashboard_data/     # SQL queries and connection
├── services/                        # Additional services
│   └── analytics_chat/             # Slack bot for conversational analytics
│       ├── main.py                  # Flask app for Slack integration
│       └── Dockerfile               # Container deployment
├── tests/                          # Test suite
│   ├── test_pipeline.py            # Integration tests
│   ├── test_dashboard.py           # Dashboard validation
│   └── test_funnel_query.py        # Query testing
├── pyproject.toml                  # Python dependencies and config
└── docs/                           # Documentation and assets
    ├── architecture.png
    └── demo_dashboard.gif
```

## Dashboard Features

The dashboard provides comprehensive ecommerce analytics enhanced with AI-powered insights:

### Key Visualizations
- **Monthly Active Users (MAU)**: Trend of user activity over time
- **Cohort Retention**: User retention analysis by registration cohort  
- **Geographic Distribution**: World map of users by country with growth/decline indicators
- **Platform Analysis**: User distribution across Android, iOS, Desktop, Web
- **Shopping Funnel**: 5-step conversion funnel analysis with detailed metrics
- **🤖 AI Insights**: Automated analysis and recommendations powered by Vertex AI Gemini

### AI-Powered Features
- **Automated Summaries**: Daily AI-generated insights highlighting key trends
- **Conversational Analytics**: Slack bot for natural language queries
- **Smart Notifications**: Automated alerts for significant metric changes
- **Trend Analysis**: AI identifies patterns and anomalies in the data

### Data Quality
- Monthly metrics exclude the current (potentially partial) month
- Funnel analysis uses the latest complete month
- Retention analysis focuses on the 5 most recent cohorts
- All data is sourced from the reliable BigQuery public dataset

## Development Setup

### Requirements

- Python 3.12
- Google Cloud Project with BigQuery and Vertex AI APIs enabled
- Service account with BigQuery read permissions and Vertex AI access
- Node.js (for Evidence.dev dashboard)
- Optional: Slack workspace for conversational analytics
- Optional: SendGrid account for email notifications

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
# Core Google Cloud Configuration
GCP_PROJECT=your-google-cloud-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Vertex AI Configuration
VERTEX_LOCATION=us-central1
VERTEX_MODEL=gemini-1.5-flash
BQ_DATASET=ecommerce_analytics

# Optional: Slack Integration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=analytics-alerts
SLACK_SIGNING_SECRET=your-slack-signing-secret

# Optional: Email Notifications
EMAIL_API_KEY=your-sendgrid-api-key
EMAIL_TO=analytics@yourcompany.com
EMAIL_FROM=noreply@yourcompany.com
```

### dbt Configuration

Update `pipeline/transform/ecommerce_metrics/profiles.yml` with your GCP project details.

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
cd pipeline/transform/ecommerce_metrics
dbt build

# Export to DuckDB only  
python pipeline/export/export_to_duckdb.py

# AI summarizer only (requires Cloud Run or local setup)
python pipeline/gemini_summarizer/main.py

# Evidence dashboard only
cd dashboard
npm run dev

# Slack bot only
python services/analytics_chat/main.py
```

## Pipeline Stages

The enhanced Dagster pipeline consists of 5 main assets:

1. **dbt Transformation** (`ecommerce_dbt_assets`)
   - Processes BigQuery public dataset
   - Creates analytics-ready models (MAU, retention, platform share, etc.)
   - Materializes tables in your BigQuery project

2. **DuckDB Export** (`export_to_duckdb`)  
   - Exports all dbt models from BigQuery to local DuckDB
   - Optimizes for fast Evidence.dev query performance

3. **AI Analysis** (`gemini_summary`)
   - Triggers Cloud Run job for Vertex AI analysis
   - Generates automated insights using Gemini LLM
   - Stores summaries in BigQuery with structured facts

4. **Summary Sync** (`sync_summary`) 
   - Syncs AI-generated summaries from BigQuery to DuckDB
   - Makes insights available to Evidence.dev dashboard

5. **Dashboard Build** (`evidence_dashboard`)
   - Builds Evidence.dev dashboard with fresh data and AI insights
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

## Additional Services

### Slack Analytics Bot
The project includes a Flask-based Slack bot that provides conversational analytics:

- **Natural Language Queries**: Ask questions like "What's our retention rate?" or "How is mobile performing?"
- **Real-time Data**: Queries live data from BigQuery for up-to-date insights  
- **Interactive Commands**: Use `/analytics ask "your question"` in Slack
- **Contextual Responses**: AI-powered responses using current analytics data

### AI Summarizer Service
A containerized service that generates automated insights:

- **Daily Analysis**: Scheduled analysis of key metrics and trends
- **Vertex AI Integration**: Uses Google's Gemini models for intelligent summaries
- **Structured Output**: Generates both narrative summaries and structured facts
- **Multi-channel Delivery**: Supports Slack, email, and dashboard integration

### Testing Suite
Comprehensive test coverage for reliability:

- **Pipeline Tests**: Validates end-to-end data pipeline execution
- **Dashboard Tests**: Checks Evidence.dev configuration and data quality
- **Query Tests**: Validates SQL logic and funnel analysis accuracy

## Contributing

1. Fork the repository
2. Create feature branch
3. Add your improvements
4. Test the complete pipeline
5. Submit pull request

## License

MIT License - see LICENSE file for details.