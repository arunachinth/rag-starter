import boto3
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'us-east-1'))

def delete_knowledge_base():
    """Clean up resources"""
    kb_id = os.getenv('KNOWLEDGE_BASE_ID')
    if kb_id:
        try:
            client.delete_knowledge_base(knowledgeBaseId=kb_id)
            print(f"Deleted Knowledge Base: {kb_id}")
        except Exception as e:
            print(f"Error deleting KB: {e}")

if __name__ == "__main__":
    delete_knowledge_base()
