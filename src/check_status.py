import boto3
import os
import sys
from dotenv import load_dotenv

load_dotenv()

client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'us-east-1'))

kb_id = os.getenv('KNOWLEDGE_BASE_ID')
ds_id = os.getenv('DATA_SOURCE_ID')

if not kb_id or not ds_id:
    print("Set KNOWLEDGE_BASE_ID and DATA_SOURCE_ID in .env")
    exit(1)

# Get latest ingestion job
response = client.list_ingestion_jobs(
    knowledgeBaseId=kb_id,
    dataSourceId=ds_id,
    maxResults=1
)

if not response['ingestionJobSummaries']:
    print("No ingestion jobs found")
    exit(0)

job = response['ingestionJobSummaries'][0]
print(f"Job ID: {job['ingestionJobId']}")
print(f"Status: {job['status']}")
print(f"Started: {job['startedAt']}")

if 'statistics' in job:
    stats = job['statistics']
    print(f"\nDocuments:")
    print(f"  Scanned: {stats.get('numberOfDocumentsScanned', 0)}")
    print(f"  Indexed: {stats.get('numberOfDocumentsIndexed', 0)}")
    print(f"  Failed: {stats.get('numberOfDocumentsFailed', 0)}")
