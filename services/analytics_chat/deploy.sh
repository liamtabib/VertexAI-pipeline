#!/bin/bash

# Deployment script for Analytics Chat Service
set -e

echo "🚀 Deploying Analytics Chat Service to Cloud Run"
echo "=============================================="

# Configuration
PROJECT_ID="pipeline-466508"
REGION="us-central1"
SERVICE_NAME="analytics-chat"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/gemini-summarizer/${SERVICE_NAME}"

# Build Docker image
echo "📦 Building Docker image..."
docker build --platform linux/amd64 -t ${IMAGE_NAME} .

# Push to Container Registry
echo "📤 Pushing to Container Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=1 \
    --timeout=60s \
    --concurrency=10 \
    --max-instances=5 \
    --set-env-vars="GCP_PROJECT=${PROJECT_ID},VERTEX_LOCATION=${REGION},VERTEX_MODEL=gemini-2.0-flash-001,BQ_DATASET=ecommerce_analytics,SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo ""
echo "✅ Deployment complete!"
echo "📍 Service URL: ${SERVICE_URL}"
echo "🔧 Slack Command URL: ${SERVICE_URL}/slack/command"
echo ""
echo "📋 Next steps:"
echo "1. Update your Slack app's slash command URL to: ${SERVICE_URL}/slack/command"
echo "2. Test with: /product_analytics ask \"What's our current MAU?\""
echo "3. Check logs: gcloud logs read --service=${SERVICE_NAME} --region=${REGION}"