#!/bin/bash
set -e

# Load environment variables
source .env

echo "Building SAM application..."
sam build

echo "Deploying to AWS..."
sam deploy \
  --stack-name rag-api \
  --parameter-overrides \
    KnowledgeBaseId=$KNOWLEDGE_BASE_ID \
    DataSourceId=$DATA_SOURCE_ID \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-confirm-changeset

echo "Deployment complete!"
echo "Getting API endpoint..."
aws cloudformation describe-stacks \
  --stack-name rag-api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text
