import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = boto3.client('bedrock-agent-runtime', region_name=os.getenv('AWS_REGION', 'us-east-1'))

HISTORY_FILE = '.chat_history.json'

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history[-10:], f, indent=2)  # Keep last 10 exchanges

def query_rag(query, knowledge_base_id, session_id):
    response = client.retrieve_and_generate(
        input={'text': query},
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': knowledge_base_id,
                'modelArn': f"arn:aws:bedrock:{os.getenv('AWS_REGION')}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
            }
        },
        sessionId=session_id
    )
    return response['output']['text'], response['sessionId']

if __name__ == "__main__":
    kb_id = os.getenv('KNOWLEDGE_BASE_ID')
    
    if not kb_id:
        print("Set KNOWLEDGE_BASE_ID in .env")
        exit(1)
    
    history = load_history()
    session_id = history[-1]['session_id'] if history else None
    
    print(f"\n{'='*60}")
    print("RAG Chat (type 'exit' to quit, 'clear' to reset history)")
    print(f"{'='*60}\n")
    
    while True:
        query = input("You: ").strip()
        
        if query.lower() == 'exit':
            break
        if query.lower() == 'clear':
            history = []
            session_id = None
            save_history(history)
            print("History cleared.\n")
            continue
        if not query:
            continue
        
        answer, session_id = query_rag(query, kb_id, session_id)
        
        history.append({'query': query, 'answer': answer, 'session_id': session_id})
        save_history(history)
        
        print(f"\nAssistant: {answer}\n")
        print(f"{'-'*60}\n")
