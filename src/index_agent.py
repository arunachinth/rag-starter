import boto3
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'us-east-1'))

def index_documents(knowledge_base_id, data_source_id):
    response = client.start_ingestion_job(
        knowledgeBaseId=knowledge_base_id,
        dataSourceId=data_source_id
    )
    print(f"Ingestion job started: {response['ingestionJob']['ingestionJobId']}")
    return response['ingestionJob']['ingestionJobId']

if __name__ == "__main__":
    kb_id = os.getenv('KNOWLEDGE_BASE_ID')
    ds_id = os.getenv('DATA_SOURCE_ID')
    
    if not kb_id or not ds_id:
        print("Set KNOWLEDGE_BASE_ID and DATA_SOURCE_ID in .env")
        exit(1)
    
    index_documents(kb_id, ds_id)
