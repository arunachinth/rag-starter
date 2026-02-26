# REST API Response Examples with Validation

## Example 1: High Confidence (Valid Response)

### Request
```bash
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/Prod/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query",
    "query": "I am a police officer with 15 years of service in Los Angeles County. How many vacation days do I get?"
  }'
```

### Response (200 OK)
```json
{
  "success": true,
  "query": "I am a police officer with 15 years of service in Los Angeles County. How many vacation days do I get?",
  "enhanced_query": "What are the vacation day entitlements for a police officer with 15 years of service in Los Angeles County, California?",
  "entities": {
    "department": "police",
    "years_of_service": 15,
    "county": "Los Angeles",
    "state": "California"
  },
  "answer": "Based on your profile as a police officer with 15 years of service in Los Angeles County, you are entitled to 20 days of paid vacation per year. According to the LA County police benefits policy, officers with 10-20 years of service receive this benefit. You can carry over up to 5 unused days to the next year.",
  "validation": {
    "is_valid": true,
    "confidence": 0.98,
    "issues": [],
    "supported_claims": [
      "20 days of paid vacation for officers with 10-20 years of service",
      "15 years falls within 10-20 year range",
      "5 days carryover allowed",
      "Policy applies to Los Angeles County police"
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
  "timestamp": "2026-02-26T06:45:00Z"
}
```

---

## Example 2: Low Confidence (Hallucinated Response)

### Request
```bash
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/Prod/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query",
    "query": "What percentage of my salary will I get when I retire with 15 years?",
    "session_id": "session-1709012345"
  }'
```

### Response (200 OK)
```json
{
  "success": true,
  "query": "What percentage of my salary will I get when I retire with 15 years?",
  "enhanced_query": "What percentage of salary does a police officer with 15 years of service in Los Angeles County receive at retirement?",
  "entities": {
    "department": "police",
    "years_of_service": 15,
    "county": "Los Angeles",
    "state": "California"
  },
  "answer": "With 15 years of service, you will receive 75% of your highest salary when you retire at age 60. This is based on the California police pension formula.",
  "validation": {
    "is_valid": false,
    "confidence": 0.35,
    "issues": [
      "Percentage claim (75%) not found in source documents",
      "Correct calculation: 15 years × 2.5% = 37.5%, not 75%",
      "Response contradicts documented formula"
    ],
    "supported_claims": [
      "Retirement benefits available for California police",
      "Age 60 mentioned for full benefits"
    ],
    "unsupported_claims": [
      "75% of highest salary for 15 years of service"
    ]
  },
  "sources": [
    {
      "source": "s3://team3-policy-documents/retirement-police-ca.pdf",
      "relevance": 0.89
    }
  ],
  "session_id": "session-1709012345",
  "timestamp": "2026-02-26T06:46:00Z"
}
```

**Frontend Action**: Display warning banner with unsupported claims, suggest contacting HR.

---

## Example 3: Medium Confidence (Partial Accuracy)

### Request
```bash
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/Prod/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query",
    "query": "What benefits do I get as a fire department employee with 12 years in San Diego?"
  }'
```

### Response (200 OK)
```json
{
  "success": true,
  "query": "What benefits do I get as a fire department employee with 12 years in San Diego?",
  "enhanced_query": "What are the benefits for a fire department employee with 12 years of service in San Diego County?",
  "entities": {
    "department": "fire",
    "years_of_service": 12,
    "county": "San Diego",
    "state": "California"
  },
  "answer": "As a fire department employee with 12 years of service in San Diego, you receive: 18 days of paid vacation annually, full health insurance coverage for you and your family, retirement at 3% per year (36% at 12 years), $500 annual uniform allowance, and free gym membership at county facilities.",
  "validation": {
    "is_valid": false,
    "confidence": 0.65,
    "issues": [
      "Uniform allowance ($500) not mentioned in source documents",
      "Gym membership not found in retrieved documents"
    ],
    "supported_claims": [
      "18 days vacation for 10-15 years of service",
      "Full health insurance for employee and family",
      "3% per year retirement formula",
      "36% calculation correct (12 × 3%)"
    ],
    "unsupported_claims": [
      "$500 annual uniform allowance",
      "Free gym membership at county facilities"
    ]
  },
  "sources": [
    {
      "source": "s3://team3-policy-documents/fire-benefits-san-diego.pdf",
      "relevance": 0.91
    },
    {
      "source": "s3://team3-policy-documents/health-insurance-policy.pdf",
      "relevance": 0.84
    }
  ],
  "session_id": "session-1709012346",
  "timestamp": "2026-02-26T06:46:30Z"
}
```

**Frontend Action**: Display verified claims normally, mark unsupported claims with disclaimer icon.

---

## Example 4: Follow-up Query (Context Maintained)

### Request
```bash
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/Prod/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query",
    "query": "What if I had 20 years instead?",
    "session_id": "session-1709012345"
  }'
```

### Response (200 OK)
```json
{
  "success": true,
  "query": "What if I had 20 years instead?",
  "enhanced_query": "What are the vacation benefits for a police officer with 20 years of service in Los Angeles County, California?",
  "entities": {
    "department": "police",
    "years_of_service": 20,
    "county": "Los Angeles",
    "state": "California"
  },
  "answer": "With 20 years of service instead of 15, your vacation benefits improve. You would receive 25 days of paid vacation per year, as officers with 20+ years of service fall into the higher tier. You can still carry over up to 5 unused days to the next year.",
  "validation": {
    "is_valid": true,
    "confidence": 0.96,
    "issues": [],
    "supported_claims": [
      "25 days of paid vacation for officers with 20+ years of service",
      "20 years qualifies for higher tier",
      "5 days carryover policy unchanged"
    ],
    "unsupported_claims": []
  },
  "sources": [
    {
      "source": "s3://team3-policy-documents/police-benefits-la-county.pdf",
      "relevance": 0.94
    }
  ],
  "session_id": "session-1709012345",
  "timestamp": "2026-02-26T06:47:00Z"
}
```

**Note**: System updated `years_of_service` from 15 to 20 and provided new calculation.

---

## Example 5: Missing Information

### Request
```bash
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/Prod/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query",
    "query": "What are my benefits?"
  }'
```

### Response (200 OK)
```json
{
  "success": true,
  "query": "What are my benefits?",
  "enhanced_query": "What are my benefits?",
  "entities": {},
  "answer": "I'd be happy to help you understand your benefits, but I need some additional information to provide accurate details. Could you please tell me: 1) Which department do you work in (police, fire, public works, etc.)? 2) How many years of service do you have? 3) Which county and state are you located in? This will help me provide benefits specific to your situation.",
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
  "session_id": "session-1709012347",
  "timestamp": "2026-02-26T06:47:30Z"
}
```

**Frontend Action**: Display form to collect department, years, location.

---

## Example 6: Cross-Department Error (Detected)

### Request
```bash
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/Prod/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query",
    "query": "What is my retirement age as a police officer with 20 years?"
  }'
```

### Response (200 OK)
```json
{
  "success": true,
  "query": "What is my retirement age as a police officer with 20 years?",
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
  "session_id": "session-1709012348",
  "timestamp": "2026-02-26T06:48:00Z"
}
```

**Frontend Action**: Show error banner, suggest regenerating query or contacting HR.

---

## Frontend Integration Example

### React Component
```javascript
function ResponseDisplay({ response }) {
  const { answer, validation, sources } = response;
  
  // Determine badge and styling based on validation
  const getBadge = () => {
    if (validation.is_valid && validation.confidence > 0.9) {
      return <Badge color="green">✓ Verified (98%)</Badge>;
    } else if (validation.confidence > 0.7) {
      return <Badge color="yellow">⚠ Partially Verified (65%)</Badge>;
    } else {
      return <Badge color="red">✗ Unverified (35%)</Badge>;
    }
  };
  
  return (
    <div className="response-container">
      <div className="response-header">
        {getBadge()}
        <span className="timestamp">{response.timestamp}</span>
      </div>
      
      <div className="response-body">
        <p>{answer}</p>
      </div>
      
      {/* Show validation details if not fully valid */}
      {(!validation.is_valid || validation.confidence < 0.9) && (
        <div className="validation-details">
          <h4>Validation Details</h4>
          
          {validation.issues.length > 0 && (
            <div className="issues">
              <strong>Issues Found:</strong>
              <ul>
                {validation.issues.map((issue, i) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </div>
          )}
          
          {validation.unsupported_claims.length > 0 && (
            <div className="unsupported">
              <strong>Unsupported Claims:</strong>
              <ul>
                {validation.unsupported_claims.map((claim, i) => (
                  <li key={i}>{claim}</li>
                ))}
              </ul>
              <p className="warning">
                ⚠️ Please verify these details with HR before making decisions.
              </p>
            </div>
          )}
        </div>
      )}
      
      {/* Show sources */}
      <div className="sources">
        <h4>Sources</h4>
        {sources.map((source, i) => (
          <div key={i} className="source-item">
            <span className="source-name">{source.source.split('/').pop()}</span>
            <span className="relevance">{(source.relevance * 100).toFixed(0)}% relevant</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Key Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | API call succeeded |
| `query` | string | Original user query |
| `enhanced_query` | string | Context-enriched query used for retrieval |
| `entities` | object | Extracted user profile (department, years, location) |
| `answer` | string | Generated response |
| `validation.is_valid` | boolean | Response is accurate and supported |
| `validation.confidence` | float | Confidence score (0.0-1.0) |
| `validation.issues` | array | Problems found during validation |
| `validation.supported_claims` | array | Claims backed by documents |
| `validation.unsupported_claims` | array | Claims not found in documents |
| `sources` | array | Source documents with relevance scores |
| `session_id` | string | Session ID for conversation continuity |
| `timestamp` | string | ISO 8601 timestamp |

---

## HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Query processed successfully (even if validation fails) |
| 400 | Bad Request | Missing `action` or `query` field |
| 500 | Server Error | Lambda timeout, Bedrock error, DynamoDB failure |

**Note**: Validation failures return 200 OK with `is_valid: false` in the response body, not HTTP errors.
