import boto3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

region = os.getenv('AWS_REGION', 'us-east-1')
bucket_name = os.getenv('S3_BUCKET', 'team3-policy-documents')

bedrock_agent = boto3.client('bedrock-agent', region_name=region)
aoss = boto3.client('opensearchserverless', region_name=region)
iam = boto3.client('iam', region_name=region)

# Create IAM role for Bedrock
role_name = 'BedrockKnowledgeBaseRole'
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "bedrock.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

try:
    role_response = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy)
    )
    role_arn = role_response['Role']['Arn']
    print(f"Created IAM role: {role_arn}")
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName=role_name)['Role']['Arn']
    print(f"Using existing IAM role: {role_arn}")

# Attach policies
policy_doc = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": [f"arn:aws:s3:::{bucket_name}/*", f"arn:aws:s3:::{bucket_name}"]
        },
        {
            "Effect": "Allow",
            "Action": ["bedrock:InvokeModel"],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": ["aoss:APIAccessAll"],
            "Resource": "*"
        }
    ]
}

try:
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName='BedrockKBPolicy',
        PolicyDocument=json.dumps(policy_doc)
    )
    print("Attached inline policy to role")
except Exception as e:
    print(f"Policy attachment: {e}")

time.sleep(10)  # Wait for IAM propagation

# Create OpenSearch Serverless collection
collection_name = 'policy-docs-kb'

# Create encryption policy
encryption_policy = {
    "Rules": [{
        "ResourceType": "collection",
        "Resource": [f"collection/{collection_name}"]
    }],
    "AWSOwnedKey": True
}

try:
    aoss.create_security_policy(
        name=f'{collection_name}-enc',
        type='encryption',
        policy=json.dumps(encryption_policy)
    )
    print("Created encryption policy")
except aoss.exceptions.ConflictException:
    print("Encryption policy already exists")

# Create network policy
network_policy = [{
    "Rules": [{
        "ResourceType": "collection",
        "Resource": [f"collection/{collection_name}"]
    }],
    "AllowFromPublic": True
}]

try:
    aoss.create_security_policy(
        name=f'{collection_name}-net',
        type='network',
        policy=json.dumps(network_policy)
    )
    print("Created network policy")
except aoss.exceptions.ConflictException:
    print("Network policy already exists")

try:
    collection_response = aoss.create_collection(
        name=collection_name,
        type='VECTORSEARCH'
    )
    collection_arn = collection_response['createCollectionDetail']['arn']
    collection_id = collection_response['createCollectionDetail']['id']
    print(f"Created OpenSearch collection: {collection_arn}")
    
    # Wait for collection to be active
    while True:
        status = aoss.batch_get_collection(ids=[collection_id])['collectionDetails'][0]['status']
        if status == 'ACTIVE':
            break
        print(f"Waiting for collection to be active... (status: {status})")
        time.sleep(10)
except aoss.exceptions.ConflictException:
    collections = aoss.list_collections(collectionFilters={'name': collection_name})['collectionSummaries']
    collection_arn = collections[0]['arn']
    print(f"Using existing collection: {collection_arn}")

# Create data access policy
sts = boto3.client('sts')
caller_identity = sts.get_caller_identity()
current_user_arn = caller_identity['Arn']

access_policy = [{
    "Rules": [{
        "ResourceType": "collection",
        "Resource": [f"collection/{collection_name}"],
        "Permission": ["aoss:*"]
    }, {
        "ResourceType": "index",
        "Resource": [f"index/{collection_name}/*"],
        "Permission": ["aoss:*"]
    }],
    "Principal": [role_arn, current_user_arn]
}]

try:
    aoss.create_access_policy(
        name=f'{collection_name}-access',
        type='data',
        policy=json.dumps(access_policy)
    )
    print("Created data access policy")
except aoss.exceptions.ConflictException:
    try:
        existing = aoss.get_access_policy(name=f'{collection_name}-access', type='data')
        aoss.update_access_policy(
            name=f'{collection_name}-access',
            type='data',
            policyVersion=existing['accessPolicyDetail']['policyVersion'],
            policy=json.dumps(access_policy)
        )
        print("Updated data access policy")
    except Exception as e:
        if 'No changes detected' in str(e):
            print("Data access policy already correct")
        else:
            raise

print("Waiting for access policy to propagate...")
time.sleep(30)

# Get collection endpoint
collections = aoss.batch_get_collection(names=[collection_name])['collectionDetails']
collection_endpoint = collections[0]['collectionEndpoint']
print(f"Collection endpoint: {collection_endpoint}")

# Create the vector index in OpenSearch
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region, 'aoss')

os_client = OpenSearch(
    hosts=[{'host': collection_endpoint.replace('https://', ''), 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300
)

index_name = 'policy-docs-index'
index_body = {
    "settings": {"index.knn": True},
    "mappings": {
        "properties": {
            "vector": {"type": "knn_vector", "dimension": 1536, "method": {"engine": "faiss", "space_type": "l2", "name": "hnsw"}},
            "text": {"type": "text"},
            "metadata": {"type": "text"}
        }
    }
}

try:
    if os_client.indices.exists(index=index_name):
        print(f"Deleting existing index {index_name} to recreate with FAISS...")
        os_client.indices.delete(index=index_name)
        time.sleep(5)
    
    result = os_client.indices.create(index=index_name, body=index_body)
    print(f"Created index with FAISS: {index_name}")
except Exception as e:
    print(f"Index operation error: {e}")
    print("Attempting to continue anyway...")

print("Waiting for index to be ready...")
time.sleep(20)

# Verify index exists
try:
    exists = os_client.indices.exists(index=index_name)
    print(f"Index exists check: {exists}")
except Exception as e:
    print(f"Cannot verify index: {e}")

# Create Knowledge Base
kb_response = bedrock_agent.create_knowledge_base(
    name='PolicyDocsKB',
    roleArn=role_arn,
    knowledgeBaseConfiguration={
        'type': 'VECTOR',
        'vectorKnowledgeBaseConfiguration': {
            'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1'
        }
    },
    storageConfiguration={
        'type': 'OPENSEARCH_SERVERLESS',
        'opensearchServerlessConfiguration': {
            'collectionArn': collection_arn,
            'vectorIndexName': 'policy-docs-index',
            'fieldMapping': {
                'vectorField': 'vector',
                'textField': 'text',
                'metadataField': 'metadata'
            }
        }
    }
)

kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
print(f"Created Knowledge Base: {kb_id}")

# Create Data Source
ds_response = bedrock_agent.create_data_source(
    knowledgeBaseId=kb_id,
    name='S3PolicyDocs',
    dataSourceConfiguration={
        'type': 'S3',
        's3Configuration': {
            'bucketArn': f'arn:aws:s3:::{bucket_name}'
        }
    }
)

ds_id = ds_response['dataSource']['dataSourceId']
print(f"Created Data Source: {ds_id}")

# Update .env file
env_content = f"""AWS_REGION={region}
S3_BUCKET={bucket_name}
KNOWLEDGE_BASE_ID={kb_id}
DATA_SOURCE_ID={ds_id}
"""

with open('.env', 'w') as f:
    f.write(env_content)

print("\n✓ Setup complete! .env file updated with:")
print(f"  KNOWLEDGE_BASE_ID={kb_id}")
print(f"  DATA_SOURCE_ID={ds_id}")
