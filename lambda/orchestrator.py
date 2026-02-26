import json
import boto3
import os

bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=os.environ['AWS_REGION'])
bedrock_agent = boto3.client('bedrock-agent', region_name=os.environ['AWS_REGION'])

KB_ID = os.environ['KNOWLEDGE_BASE_ID']
DS_ID = os.environ['DATA_SOURCE_ID']

def query_rag(query, session_id=None):
    params = {
        'input': {'text': query},
        'retrieveAndGenerateConfiguration': {
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': KB_ID,
                'modelArn': f"arn:aws:bedrock:{os.environ['AWS_REGION']}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
            }
        }
    }
    if session_id:
        params['sessionId'] = session_id
    
    response = bedrock_runtime.retrieve_and_generate(**params)
    
    # Extract citations if available
    citations = []
    if 'citations' in response:
        for citation in response['citations'][:3]:  # Top 3 sources
            if 'retrievedReferences' in citation:
                for ref in citation['retrievedReferences']:
                    citations.append({
                        'source': ref.get('location', {}).get('s3Location', {}).get('uri', 'Unknown'),
                        'excerpt': ref.get('content', {}).get('text', '')[:200] + '...'
                    })
    
    return {
        'success': True,
        'query': query,
        'answer': response['output']['text'],
        'session_id': response['sessionId'],
        'sources': citations if citations else None,
        'timestamp': response['ResponseMetadata']['HTTPHeaders']['date']
    }

def start_ingestion():
    response = bedrock_agent.start_ingestion_job(
        knowledgeBaseId=KB_ID,
        dataSourceId=DS_ID
    )
    return {
        'success': True,
        'message': 'Document ingestion started successfully',
        'job_id': response['ingestionJob']['ingestionJobId'],
        'status': response['ingestionJob']['status']
    }

def check_ingestion_status():
    response = bedrock_agent.list_ingestion_jobs(
        knowledgeBaseId=KB_ID,
        dataSourceId=DS_ID,
        maxResults=1
    )
    if not response['ingestionJobSummaries']:
        return {
            'success': True,
            'status': 'NO_JOBS',
            'message': 'No ingestion jobs found'
        }
    
    job = response['ingestionJobSummaries'][0]
    stats = job.get('statistics', {})
    
    status_messages = {
        'IN_PROGRESS': 'Ingestion is currently in progress',
        'COMPLETE': 'Ingestion completed successfully',
        'FAILED': 'Ingestion failed. Please check logs'
    }
    
    return {
        'success': True,
        'job_id': job['ingestionJobId'],
        'status': job['status'],
        'message': status_messages.get(job['status'], 'Unknown status'),
        'documents': {
            'scanned': stats.get('numberOfDocumentsScanned', 0),
            'indexed': stats.get('numberOfDocumentsIndexed', 0),
            'failed': stats.get('numberOfDocumentsFailed', 0)
        }
    }

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')
        
        if action == 'query':
            result = query_rag(body['query'], body.get('session_id'))
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        
        elif action == 'index':
            result = start_ingestion()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        
        elif action == 'status':
            result = check_ingestion_status()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': False,
                    'error': 'Invalid action',
                    'message': 'Action must be one of: query, index, or status'
                })
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'message': str(e)
            })
        }
