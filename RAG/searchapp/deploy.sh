#!/bin/bash

# Deployment script for TechTrapture Search App to Cloud Run

PROJECT_ID="tt-workshop-00"
SERVICE_NAME="techtrapture-search"
REGION="us-central1"

echo "🚀 Deploying TechTrapture Search App to Cloud Run..."
echo "📍 Project: $PROJECT_ID"
echo "📍 Service: $SERVICE_NAME"
echo "📍 Region: $REGION"
echo ""

# Set the project
gcloud config set project $PROJECT_ID

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --port 8080

echo ""
echo "✅ Deployment complete!"
echo "🌐 Your app should be available at the URL shown above"
