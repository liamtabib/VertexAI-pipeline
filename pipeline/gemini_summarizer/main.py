import os, json, re, time, signal, sys, logging
from datetime import date
from google.cloud import bigquery
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from slack_sdk import WebClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Load environment variables for testing
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure structured logging for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, _):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# ENV (set via Cloud Run Job env vars)
PROJECT      = os.environ["GCP_PROJECT"]
LOCATION     = os.environ.get("VERTEX_LOCATION", "us-central1")
MODEL_ID     = os.environ.get("VERTEX_MODEL", "gemini-1.5-flash")
BQ_DATASET   = os.environ.get("BQ_DATASET", "ecommerce_analytics")
RUN_ID       = os.environ.get("RUN_ID") or time.strftime("%Y-%m-%d")

SLACK_TOKEN  = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CH     = os.environ.get("SLACK_CHANNEL", "")
EMAIL_KEY    = os.environ.get("EMAIL_API_KEY", "")
EMAIL_TO     = os.environ.get("EMAIL_TO", "")
EMAIL_FROM   = os.environ.get("EMAIL_FROM", "")

# Queries reference current PROJECT + BQ_DATASET (using actual dbt model names)
SQLS = {
  "mau":                 "SELECT month, mau FROM `{PROJECT}.{BQ_DATASET}.mau` ORDER BY month DESC LIMIT 18",
  "retention":           "SELECT * FROM `{PROJECT}.{BQ_DATASET}.retention`",
  "platform":            "SELECT platform, users, share FROM `{PROJECT}.{BQ_DATASET}.platform_share`",
  "funnel":              "SELECT step, step_name, sessions FROM `{PROJECT}.{BQ_DATASET}.funnel` ORDER BY step",
  "kpi_metrics":         "SELECT * FROM `{PROJECT}.{BQ_DATASET}.kpi_metrics`",
  "data_end_date":       "SELECT data_end_date FROM `{PROJECT}.{BQ_DATASET}.data_end_date`"
}

def _fmt(sql: str) -> str:
    return sql.format(PROJECT=PROJECT, BQ_DATASET=BQ_DATASET)

def _norm(rows):
    out=[]
    for r in rows:
        d = dict(r)
        for k,v in d.items():
            if isinstance(v, date): d[k] = str(v)
        out.append(d)
    return out

def fetch_payload():
    """Fetch analytics data from BigQuery"""
    logger.info("Fetching analytics data from BigQuery...")
    
    try:
        bq = bigquery.Client(project=PROJECT)
        data = {}
        
        # Execute queries with error handling
        for key, query in SQLS.items():
            logger.info(f"Executing query: {key}")
            result = list(bq.query(_fmt(query)).result())
            data[key] = result
            logger.info(f"Query {key} returned {len(result)} rows")
        
        payload = {"run_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "sections": {}}
        payload["data_end_date"] = time.strftime("%Y-%m-%d")
        
        for k in ["mau","retention","platform","funnel","kpi_metrics"]:
            payload["sections"][k] = _norm(data[k])
        
        logger.info(f"Successfully fetched data for date: {payload['data_end_date']}")
        return payload
        
    except Exception as e:
        logger.error(f"Failed to fetch payload from BigQuery: {e}")
        raise

def call_gemini(payload, prompt_path="prompt.txt"):
    """Generate AI summary using Vertex AI Gemini"""
    logger.info(f"Initializing Vertex AI with model: {MODEL_ID}")
    
    try:
        vertexai.init(project=PROJECT, location=LOCATION)
        model = GenerativeModel(MODEL_ID)
        cfg = GenerationConfig(temperature=0.2, max_output_tokens=600)
        
        # Load prompt template - check environment variable first (from pipeline), fallback to file
        prompt_content = os.environ.get("PROMPT_CONTENT")
        if prompt_content:
            prompt = prompt_content
            logger.info("Using prompt content provided by pipeline")
        else:
            prompt = open(prompt_path, "r", encoding="utf-8").read()
            logger.info(f"Using prompt from local file: {prompt_path}")
        
        # Combine prompt with JSON data as text
        full_prompt = f"{prompt}\n\nData:\n{json.dumps(payload, indent=2)}"
        
        logger.info("Calling Vertex AI Gemini...")
        resp = model.generate_content(
            full_prompt,
            generation_config=cfg
        )
        
        summary_text = resp.text
        logger.info(f"Generated summary: {len(summary_text)} characters")
        logger.debug(f"Summary preview: {summary_text[:200]}...")
        
        return summary_text
        
    except Exception as e:
        logger.error(f"Failed to generate summary with Vertex AI: {e}")
        raise

def extract_facts(text):
    m = re.search(r"facts_json.*?({.*})", text, flags=re.S)
    try: return json.loads(m.group(1)) if m else {}
    except: return {}

def clean_summary_text(text):
    """Remove any JSON blocks or facts_json sections from summary text and fix formatting"""
    # Remove facts_json section
    text = re.sub(r"facts_json.*", "", text, flags=re.S | re.I)
    # Remove any remaining JSON code blocks
    text = re.sub(r"```json.*?```", "", text, flags=re.S | re.I)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    
    # Fix paragraph formatting - convert literal \n\n to actual line breaks
    text = text.replace("\\n\\n", "\n\n")
    text = text.replace("\\n", "\n")
    
    # Clean up extra whitespace and ensure proper paragraph spacing
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)  # No more than 2 consecutive newlines
    
    return text.strip()

def merge_summary(run_id, data_end_date, text, facts):
    bq = bigquery.Client(project=PROJECT)
    bq.query(
        f"""
        MERGE `{PROJECT}.{BQ_DATASET}.summaries` T
        USING (SELECT @run_id AS run_id, @ded AS ded, @text AS text, @facts AS facts) S
        ON T.run_id = S.run_id
        WHEN MATCHED THEN UPDATE SET data_end_date = S.ded, text = S.text, facts_json = S.facts
        WHEN NOT MATCHED THEN INSERT (run_id, data_end_date, text, facts_json) VALUES (S.run_id, S.ded, S.text, S.facts)
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("run_id","STRING", run_id),
                bigquery.ScalarQueryParameter("ded","DATE", data_end_date),
                bigquery.ScalarQueryParameter("text","STRING", text),
                bigquery.ScalarQueryParameter("facts","JSON", json.dumps(facts)),
            ]
        )
    ).result()

def send_slack(text):
    if not SLACK_TOKEN or not SLACK_CH: return None
    return WebClient(token=SLACK_TOKEN).chat_postMessage(channel=SLACK_CH, text=text)["ts"]

def send_email(text, subject):
    if not EMAIL_KEY or not EMAIL_TO or not EMAIL_FROM: return None
    sg = SendGridAPIClient(EMAIL_KEY)
    res = sg.send(Mail(from_email=EMAIL_FROM, to_emails=EMAIL_TO, subject=subject, html_content=f"<p>{text}</p>"))
    return str(res.headers.get("X-Message-Id",""))

def update_ids(run_id, slack_ts, email_id):
    if not (slack_ts or email_id): return
    bq = bigquery.Client(project=PROJECT)
    bq.query(
        f"UPDATE `{PROJECT}.{BQ_DATASET}.summaries` SET sent_slack_ts=@s, sent_email_id=@e WHERE run_id=@r",
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("s","STRING", slack_ts),
                bigquery.ScalarQueryParameter("e","STRING", email_id),
                bigquery.ScalarQueryParameter("r","STRING", run_id),
            ]
        )
    ).result()

def main():
    """Main execution function with comprehensive error handling"""
    logger.info(f"Starting Gemini summarizer with RUN_ID: {RUN_ID}")
    
    try:
        # Check for shutdown signal
        if shutdown_requested:
            logger.info("Shutdown requested, exiting gracefully")
            return
        
        # Fetch analytics data
        payload = fetch_payload()
        
        # Generate AI summary
        raw_text = call_gemini(payload)
        
        # Extract structured facts before cleaning
        facts = extract_facts(raw_text)
        logger.info(f"Extracted facts: {facts}")
        
        # Clean the text for display (remove JSON)
        clean_text = clean_summary_text(raw_text)
        logger.info(f"Cleaned summary: {clean_text}")
        
        # Store summary in BigQuery
        logger.info("Storing summary in BigQuery...")
        merge_summary(RUN_ID, payload["data_end_date"], clean_text, facts)
        logger.info("✅ Summary stored successfully")
        
        # Send notifications (optional)
        if SLACK_TOKEN and SLACK_CH:
            logger.info("Sending Slack notification...")
            slack_ts = send_slack(clean_text)
            logger.info(f"✅ Slack notification sent: {slack_ts}")
        else:
            slack_ts = None
            logger.info("⚠️ Slack notification skipped (no credentials)")
        
        if EMAIL_KEY and EMAIL_TO:
            logger.info("Sending email notification...")
            email_id = send_email(clean_text, f"Ecommerce Summary — As of {payload['data_end_date']}")
            logger.info(f"✅ Email notification sent: {email_id}")
        else:
            email_id = None
            logger.info("⚠️ Email notification skipped (no credentials)")
        
        # Update notification IDs
        if slack_ts or email_id:
            update_ids(RUN_ID, slack_ts, email_id)
            logger.info("✅ Notification IDs updated")
        
        logger.info(f"🎉 Gemini summarizer completed successfully for RUN_ID: {RUN_ID}")
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down gracefully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Gemini summarizer failed: {e}")
        logger.exception("Full error traceback:")
        sys.exit(1)

if __name__ == "__main__":
    main()