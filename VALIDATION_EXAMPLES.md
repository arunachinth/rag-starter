# API Response with Validation

## Query Example
```bash
curl -X POST https://YOUR_API_URL/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query",
    "query": "I work in the police department with 15 years of service in California. What are my vacation benefits?"
  }'
```

## Response with Validation
```json
{
  "success": true,
  "query": "I work in the police department with 15 years of service in California. What are my vacation benefits?",
  "enhanced_query": "What are the vacation benefits for a police officer with 15 years of service in California?",
  "entities": {
    "department": "police",
    "years_of_service": 15,
    "state": "California"
  },
  "answer": "Based on your profile as a police officer with 15 years of service in California, you are entitled to 20 days of paid vacation per year. According to the California police benefits policy, officers with 10-20 years of service receive this benefit. You can carry over up to 5 unused days to the next year.",
  "validation": {
    "is_valid": true,
    "confidence": 0.95,
    "issues": [],
    "supported_claims": [
      "20 days of paid vacation for 10-20 years of service",
      "5 days carryover allowed"
    ],
    "unsupported_claims": []
  },
  "sources": [
    {
      "source": "s3://team3-policy-documents/police-benefits-ca.pdf",
      "relevance": 0.89
    }
  ],
  "session_id": "session-1234567890",
  "timestamp": "2026-02-26T06:40:00Z"
}
```

## Validation Fields Explained

### `is_valid` (boolean)
- `true`: Response is accurate and supported by documents
- `false`: Response contains unsupported claims or hallucinations

### `confidence` (0.0 - 1.0)
- `0.9-1.0`: High confidence, all claims verified
- `0.7-0.9`: Good confidence, minor uncertainties
- `0.5-0.7`: Medium confidence, some unsupported claims
- `0.0-0.5`: Low confidence, significant issues

### `issues` (array)
List of problems found:
- `[]`: No issues
- `["Numerical value not found in documents"]`: Specific problems
- `["Response contradicts source material"]`: Contradictions

### `supported_claims` (array)
Claims that are backed by source documents:
```json
[
  "20 days of paid vacation for 10-20 years of service",
  "5 days carryover allowed",
  "Must submit request 2 weeks in advance"
]
```

### `unsupported_claims` (array)
Claims not found in documents (potential hallucinations):
```json
[
  "Vacation days expire after 1 year"
]
```

## Example: Invalid Response

```json
{
  "success": true,
  "query": "What are my retirement benefits?",
  "answer": "You will receive 75% of your salary at retirement...",
  "validation": {
    "is_valid": false,
    "confidence": 0.4,
    "issues": [
      "Percentage (75%) not found in source documents",
      "Documents state 50% for 20 years, not 75%"
    ],
    "supported_claims": [
      "Retirement benefits available for police officers"
    ],
    "unsupported_claims": [
      "75% of salary at retirement"
    ]
  }
}
```

## How Validation Works

1. **Claim Extraction**: Identifies factual claims in the response
2. **Document Verification**: Checks each claim against source documents
3. **Numerical Accuracy**: Verifies numbers, dates, percentages
4. **Contradiction Detection**: Identifies statements that contradict sources
5. **Confidence Scoring**: Calculates overall accuracy confidence

## Use Cases

### Frontend Display
```javascript
if (response.validation.is_valid && response.validation.confidence > 0.8) {
  // Show answer with high confidence badge
  displayAnswer(response.answer);
} else {
  // Show answer with warning
  displayAnswerWithWarning(response.answer, response.validation.issues);
}
```

### Logging & Monitoring
```javascript
if (!response.validation.is_valid) {
  logValidationFailure({
    query: response.query,
    issues: response.validation.issues,
    unsupported_claims: response.validation.unsupported_claims
  });
}
```

### Quality Assurance
Track validation metrics:
- Average confidence score
- Percentage of valid responses
- Common validation issues
- Hallucination patterns

## Benefits

1. **Trust**: Users know the response is verified
2. **Transparency**: Shows what's supported vs unsupported
3. **Quality Control**: Catches hallucinations automatically
4. **Debugging**: Identifies prompt engineering issues
5. **Compliance**: Ensures accuracy for policy information
