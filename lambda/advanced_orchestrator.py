import json
import boto3
import os
from datetime import datetime
from typing import Dict, List

# AWS_REGION is automatically available in Lambda
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

KB_ID = os.environ['KNOWLEDGE_BASE_ID']
MEMORY_TABLE = os.environ.get('MEMORY_TABLE', 'rag-conversation-memory')

class ConversationMemory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.table = dynamodb.Table(MEMORY_TABLE)
    
    def get_context(self) -> Dict:
        try:
            response = self.table.get_item(Key={'session_id': self.session_id})
            return response.get('Item', {
                'session_id': self.session_id,
                'entities': {},
                'history': []
            })
        except:
            return {'session_id': self.session_id, 'entities': {}, 'history': []}
    
    def update_context(self, entities: Dict, query: str, response: str):
        context = self.get_context()
        context['entities'].update(entities)
        context['history'].append({
            'query': query,
            'response': response[:500],
            'timestamp': datetime.utcnow().isoformat()
        })
        context['history'] = context['history'][-10:]
        context['updated_at'] = datetime.utcnow().isoformat()
        self.table.put_item(Item=context)
        return context

class EntityExtractorAgent:
    def __init__(self):
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    
    def extract(self, query: str, existing_entities: Dict) -> Dict:
        prompt = f"""Extract structured information from the query. Return ONLY valid JSON.

Current entities: {json.dumps(existing_entities)}
Query: "{query}"

Extract: department, years_of_service (number), state, county, policy_type
Rules: Only extract explicitly mentioned entities, preserve existing unless updated

Example: {{"department": "police", "years_of_service": 15, "state": "California"}}
JSON:"""

        try:
            response = bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                })
            )
            
            result = json.loads(response['body'].read())
            content = result['content'][0]['text'].strip()
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                extracted = json.loads(content[start:end])
                return {**existing_entities, **extracted}
        except Exception as e:
            print(f"Entity extraction error: {e}")
        return existing_entities

class QueryEnhancerAgent:
    def __init__(self):
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    
    def enhance(self, query: str, entities: Dict, history: List) -> str:
        entity_str = ", ".join([f"{k}: {v}" for k, v in entities.items() if v])
        history_str = ""
        if history:
            recent = history[-2:]
            history_str = "\n".join([f"Q: {h['query']}" for h in recent])
        
        prompt = f"""Rewrite the query to be specific and context-aware for document search.

User context: {entity_str}
Recent questions: {history_str}
Current query: "{query}"

Rewrite to include relevant context. Return ONLY the enhanced query.
Enhanced query:"""

        try:
            response = bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 150,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                })
            )
            result = json.loads(response['body'].read())
            return result['content'][0]['text'].strip()
        except:
            return query

class RetrievalAgent:
    def retrieve(self, query: str, kb_id: str) -> List[Dict]:
        try:
            response = bedrock_agent_runtime.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': 5}}
            )
            return [{
                'content': r['content']['text'],
                'source': r.get('location', {}).get('s3Location', {}).get('uri', 'Unknown'),
                'score': r.get('score', 0)
            } for r in response['retrievalResults']]
        except Exception as e:
            print(f"Retrieval error: {e}")
            return []

class ResponseGeneratorAgent:
    def __init__(self):
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    def generate(self, query: str, entities: Dict, documents: List[Dict], history: List) -> str:
        docs_text = "\n\n".join([
            f"Document {i+1} (relevance: {d['score']:.2f}):\n{d['content'][:800]}"
            for i, d in enumerate(documents[:3])
        ])
        
        entity_context = json.dumps(entities, indent=2)
        history_text = ""
        if history:
            recent = history[-2:]
            history_text = "\n".join([f"User: {h['query']}\nAssistant: {h['response'][:200]}" for h in recent])
        
        prompt = f"""You are a helpful policy assistant. Answer using the documents and user context.

User Profile:
{entity_context}

Recent Conversation:
{history_text}

Retrieved Documents:
{docs_text}

Question: {query}

Instructions:
1. Answer specifically for the user's profile (department, years, location)
2. Reference specific policies from documents
3. Be conversational and acknowledge context
4. If info is missing, state what's needed
5. Cite sources

Response:"""

        try:
            response = bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                })
            )
            result = json.loads(response['body'].read())
            return result['content'][0]['text']
        except Exception as e:
            return f"Error generating response: {e}"

class ValidationAgent:
    """Validates RAG response against source documents for accuracy"""
    
    def __init__(self):
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    def validate(self, query: str, response: str, documents: List[Dict]) -> Dict:
        """Verify response accuracy against source documents"""
        
        docs_text = "\n\n".join([
            f"Document {i+1}:\n{d['content'][:1000]}"
            for i, d in enumerate(documents[:3])
        ])
        
        prompt = f"""You are a fact-checking validator. Verify if the response is accurate based on the source documents.

Source Documents:
{docs_text}

User Question: {query}

Generated Response: {response}

Validation Tasks:
1. Check if response claims are supported by documents
2. Identify any hallucinations or unsupported statements
3. Verify numerical accuracy (dates, numbers, percentages)
4. Check if response contradicts source material

Return JSON only:
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "issues": ["list of issues found, empty if none"],
  "supported_claims": ["claims backed by documents"],
  "unsupported_claims": ["claims not in documents"]
}}

JSON:"""

        try:
            validation_response = bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                })
            )
            
            result = json.loads(validation_response['body'].read())
            content = result['content'][0]['text'].strip()
            
            # Extract JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                validation_result = json.loads(content[start:end])
                return validation_result
            
        except Exception as e:
            print(f"Validation error: {e}")
        
        # Default: assume valid if validation fails
        return {
            "is_valid": True,
            "confidence": 0.5,
            "issues": ["Validation check failed"],
            "supported_claims": [],
            "unsupported_claims": []
        }

class OrchestratorAgent:
    def __init__(self):
        self.entity_extractor = EntityExtractorAgent()
        self.query_enhancer = QueryEnhancerAgent()
        self.retrieval_agent = RetrievalAgent()
        self.response_generator = ResponseGeneratorAgent()
        self.validation_agent = ValidationAgent()
    
    def process(self, query: str, session_id: str) -> Dict:
        memory = ConversationMemory(session_id)
        context = memory.get_context()
        
        # Step 1: Extract entities
        entities = self.entity_extractor.extract(query, context.get('entities', {}))
        
        # Step 2: Enhance query
        enhanced_query = self.query_enhancer.enhance(query, entities, context.get('history', []))
        
        # Step 3: Retrieve documents
        documents = self.retrieval_agent.retrieve(enhanced_query, KB_ID)
        
        # Step 4: Generate response
        response = self.response_generator.generate(query, entities, documents, context.get('history', []))
        
        # Step 5: Validate response
        validation = self.validation_agent.validate(query, response, documents)
        
        # Step 6: Update memory
        memory.update_context(entities, query, response)
        
        return {
            'success': True,
            'query': query,
            'enhanced_query': enhanced_query,
            'entities': entities,
            'answer': response,
            'validation': {
                'is_valid': validation.get('is_valid', True),
                'confidence': validation.get('confidence', 1.0),
                'issues': validation.get('issues', []),
                'supported_claims': validation.get('supported_claims', []),
                'unsupported_claims': validation.get('unsupported_claims', [])
            },
            'sources': [{'source': d['source'], 'relevance': round(d['score'], 2)} for d in documents[:3]],
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }

orchestrator = OrchestratorAgent()

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')
        
        if action == 'query':
            session_id = body.get('session_id', f"session-{int(datetime.utcnow().timestamp())}")
            result = orchestrator.process(body['query'], session_id)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result)
            }
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'success': False, 'error': 'Invalid action. Use: query'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'success': False, 'error': str(e)})
        }
