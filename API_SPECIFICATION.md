# RAG API Specification v1.0

## Base URL
```
Production: https://{api-id}.execute-api.us-east-1.amazonaws.com/Prod
Staging: https://{api-id}.execute-api.us-east-1.amazonaws.com/Stage
Development: https://{api-id}.execute-api.us-east-1.amazonaws.com/Dev
```

Replace `{api-id}` with your actual API Gateway ID (provided after deployment).

---

## Authentication
Currently: None (add API Key or Cognito in production)

Future:
```
Authorization: Bearer {token}
```

---

## Endpoints

### POST /rag

Query the RAG system with conversation memory.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "action": "query",
  "query": "string (required)",
  "session_id": "string (optional)"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | Must be `"query"` |
| `query` | string | Yes | User's question (1-500 characters) |
| `session_id` | string | No | Session ID for conversation continuity. If omitted, new session created. |

**Example Request:**
```bash
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/Prod/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query",
    "query": "I work in the police department with 15 years of service in California. What are my vacation benefits?",
    "session_id": "session-1234567890"
  }'
```

#### Response

**Success (200 OK):**
```json
{
  "success": true,
  "query": "string",
  "enhanced_query": "string",
  "entities": {
    "department": "string | null",
    "years_of_service": "number | null",
    "state": "string | null",
    "county": "string | null"
  },
  "answer": "string",
  "validation": {
    "is_valid": "boolean",
    "confidence": "number (0.0-1.0)",
    "issues": ["string"],
    "supported_claims": ["string"],
    "unsupported_claims": ["string"]
  },
  "sources": [
    {
      "source": "string",
      "relevance": "number (0.0-1.0)"
    }
  ],
  "session_id": "string",
  "timestamp": "string (ISO 8601)"
}
```

**Error (400 Bad Request):**
```json
{
  "success": false,
  "error": "Invalid action. Use: query",
  "message": "string"
}
```

**Error (500 Internal Server Error):**
```json
{
  "success": false,
  "error": "Internal server error",
  "message": "string"
}
```

---

## Response Fields

### Root Level

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | `true` if request processed, `false` if error |
| `query` | string | Original user query |
| `enhanced_query` | string | Context-enriched query used for retrieval |
| `entities` | object | Extracted user profile information |
| `answer` | string | Generated response (markdown supported) |
| `validation` | object | Response validation results |
| `sources` | array | Source documents used |
| `session_id` | string | Session ID for next request |
| `timestamp` | string | ISO 8601 timestamp |

### Entities Object

| Field | Type | Description |
|-------|------|-------------|
| `department` | string \| null | User's department (police, fire, etc.) |
| `years_of_service` | number \| null | Years of service |
| `state` | string \| null | US state |
| `county` | string \| null | County name |

### Validation Object

| Field | Type | Description |
|-------|------|-------------|
| `is_valid` | boolean | `true` if response is accurate and supported |
| `confidence` | number | Confidence score (0.0-1.0) |
| `issues` | array | List of validation issues found |
| `supported_claims` | array | Claims backed by source documents |
| `unsupported_claims` | array | Claims not found in documents (potential hallucinations) |

### Sources Array

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | S3 URI of source document |
| `relevance` | number | Relevance score (0.0-1.0) |

---

## Usage Examples

### Example 1: First Query (New Session)

**Request:**
```json
{
  "action": "query",
  "query": "I am a police officer with 15 years of service in Los Angeles County. What are my vacation benefits?"
}
```

**Response:**
```json
{
  "success": true,
  "query": "I am a police officer with 15 years of service in Los Angeles County. What are my vacation benefits?",
  "enhanced_query": "What are the vacation benefits for a police officer with 15 years of service in Los Angeles County, California?",
  "entities": {
    "department": "police",
    "years_of_service": 15,
    "state": "California",
    "county": "Los Angeles"
  },
  "answer": "Based on your profile as a police officer with 15 years of service in Los Angeles County, you are entitled to **20 days of paid vacation per year**. According to the LA County police benefits policy, officers with 10-20 years of service receive this benefit. You can carry over up to **5 unused days** to the next year.",
  "validation": {
    "is_valid": true,
    "confidence": 0.98,
    "issues": [],
    "supported_claims": [
      "20 days of paid vacation for officers with 10-20 years of service",
      "15 years falls within 10-20 year range",
      "5 days carryover allowed"
    ],
    "unsupported_claims": []
  },
  "sources": [
    {
      "source": "s3://team3-policy-documents/police-benefits-la-county.pdf",
      "relevance": 0.92
    },
    {
      "source": "s3://team3-policy-documents/vacation-policy-2026.pdf",
      "relevance": 0.87
    }
  ],
  "session_id": "session-1709012345",
  "timestamp": "2026-02-26T07:00:00Z"
}
```

### Example 2: Follow-up Query (Existing Session)

**Request:**
```json
{
  "action": "query",
  "query": "What about retirement benefits?",
  "session_id": "session-1709012345"
}
```

**Response:**
```json
{
  "success": true,
  "query": "What about retirement benefits?",
  "enhanced_query": "What are the retirement benefits for a police officer with 15 years of service in Los Angeles County, California?",
  "entities": {
    "department": "police",
    "years_of_service": 15,
    "state": "California",
    "county": "Los Angeles"
  },
  "answer": "For your retirement benefits as a police officer with 15 years of service in Los Angeles County, you're eligible for the **CalPERS retirement plan**. With 15 years, you can retire at age 55 with reduced benefits, or wait until age 60 for full benefits at **2.5% per year of service**. This means at 15 years, you'd receive **37.5% of your highest salary**. You're also eligible for retiree health benefits.",
  "validation": {
    "is_valid": true,
    "confidence": 0.96,
    "issues": [],
    "supported_claims": [
      "CalPERS retirement plan for LA County police",
      "2.5% per year formula",
      "37.5% calculation correct (15 × 2.5%)",
      "Retirement ages 55 and 60 mentioned"
    ],
    "unsupported_claims": []
  },
  "sources": [
    {
      "source": "s3://team3-policy-documents/retirement-police-ca.pdf",
      "relevance": 0.94
    }
  ],
  "session_id": "session-1709012345",
  "timestamp": "2026-02-26T07:01:00Z"
}
```

### Example 3: Entity Update

**Request:**
```json
{
  "action": "query",
  "query": "What if I had 20 years instead?",
  "session_id": "session-1709012345"
}
```

**Response:**
```json
{
  "success": true,
  "query": "What if I had 20 years instead?",
  "enhanced_query": "What are the retirement benefits for a police officer with 20 years of service in Los Angeles County, California?",
  "entities": {
    "department": "police",
    "years_of_service": 20,
    "state": "California",
    "county": "Los Angeles"
  },
  "answer": "With **20 years of service** instead of 15, your retirement benefits improve significantly. You'd receive **50% of your highest salary** (20 years × 2.5%). You can still retire at age 55 with reduced benefits or age 60 for full benefits. Additionally, with 20 years, you qualify for enhanced retiree health coverage with lower premiums.",
  "validation": {
    "is_valid": true,
    "confidence": 0.97,
    "issues": [],
    "supported_claims": [
      "50% calculation correct (20 × 2.5%)",
      "Enhanced health coverage at 20 years",
      "Same retirement age options"
    ],
    "unsupported_claims": []
  },
  "sources": [
    {
      "source": "s3://team3-policy-documents/retirement-police-ca.pdf",
      "relevance": 0.95
    }
  ],
  "session_id": "session-1709012345",
  "timestamp": "2026-02-26T07:02:00Z"
}
```

### Example 4: Low Confidence Response

**Request:**
```json
{
  "action": "query",
  "query": "What percentage of my salary will I get at retirement?"
}
```

**Response:**
```json
{
  "success": true,
  "query": "What percentage of my salary will I get at retirement?",
  "enhanced_query": "What percentage of salary does an employee receive at retirement?",
  "entities": {},
  "answer": "I'd be happy to help you understand your retirement benefits, but I need some additional information to provide accurate details. Could you please tell me: 1) Which department do you work in (police, fire, public works, etc.)? 2) How many years of service do you have? 3) Which county and state are you located in? This will help me provide the exact percentage specific to your situation.",
  "validation": {
    "is_valid": true,
    "confidence": 1.0,
    "issues": [],
    "supported_claims": [
      "Request for additional information is appropriate"
    ],
    "unsupported_claims": []
  },
  "sources": [],
  "session_id": "session-1709012346",
  "timestamp": "2026-02-26T07:03:00Z"
}
```

### Example 5: Validation Failure (Hallucination Detected)

**Request:**
```json
{
  "action": "query",
  "query": "What's my retirement age as a police officer with 20 years?"
}
```

**Response:**
```json
{
  "success": true,
  "query": "What's my retirement age as a police officer with 20 years?",
  "enhanced_query": "What is the retirement age for a police officer with 20 years of service?",
  "entities": {
    "department": "police",
    "years_of_service": 20
  },
  "answer": "With 20 years of service as a police officer, you can retire at age 50 with full benefits.",
  "validation": {
    "is_valid": false,
    "confidence": 0.40,
    "issues": [
      "Age 50 applies to fire department, not police",
      "Police retirement age is 55, not 50",
      "Response mixed policies from different departments"
    ],
    "supported_claims": [
      "20 years qualifies for retirement"
    ],
    "unsupported_claims": [
      "Police officers can retire at age 50"
    ]
  },
  "sources": [
    {
      "source": "s3://team3-policy-documents/retirement-police-ca.pdf",
      "relevance": 0.88
    },
    {
      "source": "s3://team3-policy-documents/retirement-fire-ca.pdf",
      "relevance": 0.85
    }
  ],
  "session_id": "session-1709012347",
  "timestamp": "2026-02-26T07:04:00Z"
}
```

---

## Error Handling

### 400 Bad Request

**Causes:**
- Missing `action` field
- Missing `query` field
- Invalid `action` value
- Query too long (>500 characters)

**Example:**
```json
{
  "success": false,
  "error": "Invalid action. Use: query",
  "message": "The 'action' field must be set to 'query'"
}
```

### 500 Internal Server Error

**Causes:**
- Lambda timeout
- Bedrock service error
- DynamoDB unavailable
- Model invocation failure

**Example:**
```json
{
  "success": false,
  "error": "Internal server error",
  "message": "Bedrock model invocation failed: ThrottlingException"
}
```

---

## Rate Limits

| Environment | Limit | Burst |
|-------------|-------|-------|
| Development | 10 req/sec | 20 |
| Staging | 100 req/sec | 200 |
| Production | 1000 req/sec | 2000 |

**Rate Limit Response (429 Too Many Requests):**
```json
{
  "message": "Too Many Requests"
}
```

---

## Best Practices

### 1. Session Management
```javascript
// Store session_id in client state
let sessionId = null;

async function query(userQuery) {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action: 'query',
      query: userQuery,
      session_id: sessionId
    })
  });
  
  const data = await response.json();
  sessionId = data.session_id; // Store for next query
  return data;
}
```

### 2. Validation Handling
```javascript
function displayResponse(data) {
  const { answer, validation } = data;
  
  if (validation.is_valid && validation.confidence > 0.9) {
    // High confidence - display normally
    showAnswer(answer, 'verified');
  } else if (validation.confidence > 0.7) {
    // Medium confidence - show with warning
    showAnswer(answer, 'partial', validation.issues);
  } else {
    // Low confidence - show error
    showAnswer(answer, 'unverified', validation.unsupported_claims);
  }
}
```

### 3. Error Handling
```javascript
async function safeQuery(userQuery) {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'query', query: userQuery })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error);
    }
    
    return data;
  } catch (error) {
    console.error('Query failed:', error);
    return {
      success: false,
      error: error.message,
      answer: 'Sorry, I encountered an error. Please try again.'
    };
  }
}
```

### 4. Retry Logic
```javascript
async function queryWithRetry(userQuery, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await query(userQuery);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(1000 * Math.pow(2, i)); // Exponential backoff
    }
  }
}
```

---

## TypeScript Types

```typescript
// Request
interface QueryRequest {
  action: 'query';
  query: string;
  session_id?: string;
}

// Response
interface QueryResponse {
  success: boolean;
  query: string;
  enhanced_query: string;
  entities: {
    department: string | null;
    years_of_service: number | null;
    state: string | null;
    county: string | null;
  };
  answer: string;
  validation: {
    is_valid: boolean;
    confidence: number;
    issues: string[];
    supported_claims: string[];
    unsupported_claims: string[];
  };
  sources: Array<{
    source: string;
    relevance: number;
  }>;
  session_id: string;
  timestamp: string;
}

// Error Response
interface ErrorResponse {
  success: false;
  error: string;
  message: string;
}

// API Client
class RAGClient {
  constructor(private baseUrl: string) {}
  
  async query(query: string, sessionId?: string): Promise<QueryResponse> {
    const response = await fetch(`${this.baseUrl}/rag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'query',
        query,
        session_id: sessionId
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return response.json();
  }
}
```

---

## OpenAPI 3.0 Specification

```yaml
openapi: 3.0.0
info:
  title: RAG API
  version: 1.0.0
  description: Multi-agent RAG system for policy document queries

servers:
  - url: https://{api-id}.execute-api.us-east-1.amazonaws.com/Prod
    description: Production
  - url: https://{api-id}.execute-api.us-east-1.amazonaws.com/Stage
    description: Staging

paths:
  /rag:
    post:
      summary: Query the RAG system
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - action
                - query
              properties:
                action:
                  type: string
                  enum: [query]
                query:
                  type: string
                  minLength: 1
                  maxLength: 500
                session_id:
                  type: string
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  query:
                    type: string
                  enhanced_query:
                    type: string
                  entities:
                    type: object
                    properties:
                      department:
                        type: string
                        nullable: true
                      years_of_service:
                        type: number
                        nullable: true
                      state:
                        type: string
                        nullable: true
                      county:
                        type: string
                        nullable: true
                  answer:
                    type: string
                  validation:
                    type: object
                    properties:
                      is_valid:
                        type: boolean
                      confidence:
                        type: number
                        minimum: 0
                        maximum: 1
                      issues:
                        type: array
                        items:
                          type: string
                      supported_claims:
                        type: array
                        items:
                          type: string
                      unsupported_claims:
                        type: array
                        items:
                          type: string
                  sources:
                    type: array
                    items:
                      type: object
                      properties:
                        source:
                          type: string
                        relevance:
                          type: number
                          minimum: 0
                          maximum: 1
                  session_id:
                    type: string
                  timestamp:
                    type: string
                    format: date-time
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  error:
                    type: string
                  message:
                    type: string
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  error:
                    type: string
                  message:
                    type: string
```

---

## Postman Collection

Import this JSON into Postman:

```json
{
  "info": {
    "name": "RAG API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Query (New Session)",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"action\": \"query\",\n  \"query\": \"I work in the police department with 15 years of service in California. What are my vacation benefits?\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/rag",
          "host": ["{{base_url}}"],
          "path": ["rag"]
        }
      }
    },
    {
      "name": "Query (Existing Session)",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"action\": \"query\",\n  \"query\": \"What about retirement?\",\n  \"session_id\": \"{{session_id}}\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/rag",
          "host": ["{{base_url}}"],
          "path": ["rag"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/Prod"
    },
    {
      "key": "session_id",
      "value": ""
    }
  ]
}
```

---

## Support

For issues or questions:
- Email: support@example.com
- Slack: #rag-api-support
- Documentation: https://docs.example.com/rag-api

---

**Version History:**
- v1.0.0 (2026-02-26): Initial release
