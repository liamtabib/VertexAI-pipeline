import os
import json
import hmac
import hashlib
import time
import logging
from datetime import datetime

from flask import Flask, request, jsonify
from google.cloud import bigquery
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Environment variables
PROJECT_ID = os.environ.get("GCP_PROJECT", "pipeline-466508")
LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
MODEL_ID = os.environ.get("VERTEX_MODEL", "gemini-2.0-flash-001")
BQ_DATASET = os.environ.get("BQ_DATASET", "ecommerce_analytics")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel(MODEL_ID)
bq_client = bigquery.Client(project=PROJECT_ID)

def verify_slack_signature(request_body, timestamp, signature):
    """Verify request came from Slack"""
    if not SLACK_SIGNING_SECRET:
        logger.info("No Slack signing secret configured - skipping verification")
        return True  # Skip verification for initial deployment
    
    # Create signature
    sig_basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}"
    computed_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)

def fetch_latest_analytics_data():
    """Fetch current analytics data for context"""
    try:
        queries = {
            "mau": f"SELECT month, mau FROM `{PROJECT_ID}.{BQ_DATASET}.mau` ORDER BY month DESC LIMIT 6",
            "retention": f"SELECT * FROM `{PROJECT_ID}.{BQ_DATASET}.retention` ORDER BY period_number",
            "platform": f"SELECT platform, users, share FROM `{PROJECT_ID}.{BQ_DATASET}.platform_share`",
            "funnel": f"SELECT step, step_name, sessions FROM `{PROJECT_ID}.{BQ_DATASET}.funnel` ORDER BY step",
            "kpi_metrics": f"SELECT * FROM `{PROJECT_ID}.{BQ_DATASET}.kpi_metrics`",
            "data_end_date": f"SELECT data_end_date FROM `{PROJECT_ID}.{BQ_DATASET}.data_end_date`",
            "latest_summary": f"SELECT text, facts_json FROM `{PROJECT_ID}.{BQ_DATASET}.summaries` ORDER BY run_ts DESC LIMIT 1"
        }
        
        data = {}
        for key, query in queries.items():
            try:
                result = list(bq_client.query(query).result())
                # Convert to serializable format
                data[key] = []
                for row in result:
                    row_dict = dict(row)
                    # Convert dates to strings
                    for k, v in row_dict.items():
                        if hasattr(v, 'isoformat'):
                            row_dict[k] = v.isoformat()
                    data[key].append(row_dict)
            except Exception as e:
                logger.error(f"Error fetching {key}: {e}")
                data[key] = []
        
        return data
    except Exception as e:
        logger.error(f"Error fetching analytics data: {e}")
        return {}

def generate_analytics_response(user_question, analytics_data):
    """Generate AI response using Vertex AI"""
    try:
        # Create comprehensive prompt with data context
        data_summary = json.dumps(analytics_data, indent=2)
        
        prompt = f"""You are an expert ecommerce analytics assistant. Answer the user's question using the provided analytics data.

User Question: {user_question}

Current Analytics Data:
{data_summary}

Guidelines:
- Provide specific numbers and insights from the data
- Be concise and direct (aim for 1-2 paragraphs max)
- Use bullet points for key metrics when helpful
- Focus on what the data shows rather than what's missing
- Always provide actionable insights based on available metrics
- Format response for Slack (use *bold* for emphasis, avoid complex formatting)

Answer:"""

        # Generate response using Vertex AI
        config = GenerationConfig(temperature=0.3, max_output_tokens=800)
        response = model.generate_content(prompt, generation_config=config)
        
        return response.text
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"Sorry, I encountered an error analyzing your question: {str(e)}"

def format_slack_response(text, user_question):
    """Format response for Slack with nice structure"""
    formatted = f"""🔍 *{user_question}*

{text}"""
    
    return formatted

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/slack/command', methods=['POST'])
def handle_slack_command():
    """Handle /analytics slash command"""
    try:
        # Verify request signature
        timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
        signature = request.headers.get('X-Slack-Signature', '')
        
        if not verify_slack_signature(request.get_data(), timestamp, signature):
            logger.warning("Invalid Slack signature")
            return jsonify({"text": "Invalid request signature"}), 401
        
        # Check timestamp to prevent replay attacks (only if timestamp provided)
        if timestamp and timestamp.strip():
            try:
                if abs(time.time() - int(timestamp)) > 300:  # 5 minutes
                    logger.warning("Request timestamp too old")
                    return jsonify({"text": "Request timestamp too old"}), 401
            except ValueError:
                logger.warning(f"Invalid timestamp format: {timestamp}")
                # Continue processing - don't fail on timestamp issues
        
        # Parse form data
        form_data = request.form
        user_id = form_data.get('user_id')
        user_name = form_data.get('user_name')
        command = form_data.get('command')
        text = form_data.get('text', '').strip()
        channel_id = form_data.get('channel_id')
        
        logger.info(f"Slash command from {user_name}: {command} {text}")
        
        # Handle different command formats
        if not text:
            help_text = """🤖 *Analytics Chat Bot*

Usage examples:
• `/product_analytics ask "What's our current retention rate?"`
• `/product_analytics ask "Why did MAU change this month?"`
• `/product_analytics ask "How is mobile performing vs desktop?"`
• `/product_analytics ask "What are our top conversion metrics?"`

💡 Ask any question about your ecommerce analytics data!"""
            return jsonify({"response_type": "ephemeral", "text": help_text})
        
        # Parse command - look for "ask" prefix or treat whole text as question
        if text.lower().startswith('ask '):
            question = text[4:].strip().strip('"\'')
        else:
            question = text.strip().strip('"\'')
        
        if not question:
            return jsonify({
                "response_type": "ephemeral", 
                "text": "Please provide a question. Example: `/product_analytics ask \"What's our retention rate?\"`"
            })
        
        # Send immediate acknowledgment to Slack (required within 3 seconds)
        try:
            # Quick validation and immediate response
            import threading
            
            # Store response_url for delayed response
            response_url = form_data.get('response_url')
            
            if response_url:
                # Send immediate acknowledgment
                immediate_response = {
                    "response_type": "in_channel", 
                    "text": f"🔍 Analyzing your question: *{question}*\n⏳ Fetching analytics data and generating insights..."
                }
                
                # Process the actual query in background
                def process_analytics_query():
                    try:
                        logger.info("Background processing: Fetching analytics data...")
                        analytics_data = fetch_latest_analytics_data()
                        
                        logger.info("Background processing: Generating AI response...")
                        ai_response = generate_analytics_response(question, analytics_data)
                        
                        # Format for Slack
                        formatted_response = format_slack_response(ai_response, question)
                        
                        # Send delayed response to Slack
                        import requests
                        delayed_response = {
                            "response_type": "in_channel",
                            "text": formatted_response,
                            "replace_original": True  # Replace the "Analyzing..." message
                        }
                        
                        requests.post(response_url, json=delayed_response, timeout=10)
                        logger.info("Delayed response sent successfully")
                        
                    except Exception as e:
                        logger.error(f"Background processing error: {e}")
                        # Send error response
                        error_response = {
                            "response_type": "in_channel",
                            "text": f"❌ Sorry, I encountered an error analyzing your question: {str(e)}",
                            "replace_original": True
                        }
                        try:
                            requests.post(response_url, json=error_response, timeout=10)
                        except:
                            pass
                
                # Start background processing
                thread = threading.Thread(target=process_analytics_query)
                thread.daemon = True
                thread.start()
                
                # Return immediate response
                return jsonify(immediate_response)
            
            else:
                # Fallback: try to process quickly (original approach)
                logger.info("No response_url, processing synchronously...")
                
                # Quick timeout for synchronous processing
                analytics_data = fetch_latest_analytics_data()
                ai_response = generate_analytics_response(question, analytics_data)
                formatted_response = format_slack_response(ai_response, question)
                
                return jsonify({
                    "response_type": "in_channel",
                    "text": formatted_response
                })
                
        except Exception as e:
            logger.error(f"Error in slash command processing: {e}")
            return jsonify({
                "response_type": "ephemeral",
                "text": f"❌ Sorry, I encountered an error: {str(e)}"
            })
        
    except Exception as e:
        logger.error(f"Error handling slash command: {e}")
        return jsonify({
            "response_type": "ephemeral",
            "text": f"Sorry, I encountered an error: {str(e)}"
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)