# API Examples

## Query RAG
```bash
curl -X POST https://YOUR_API_URL/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query",
    "query": "What policies are available?"
  }'
```

Response:
```json
{
  "success": true,
  "query": "What policies are available?",
  "answer": "Based on the documents, the following policies are available: vacation policy, remote work policy, and expense reimbursement policy...",
  "session_id": "session-abc123",
  "sources": [
    {
      "source": "s3://team3-policy-documents/policies.pdf",
      "excerpt": "This document outlines the company policies including vacation, remote work..."
    }
  ],
  "timestamp": "Thu, 26 Feb 2026 06:17:00 GMT"
}
```

## Query with Session (Follow-up)
```bash
curl -X POST https://YOUR_API_URL/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query",
    "query": "Tell me more about that",
    "session_id": "session-abc123"
  }'
```

## Start Ingestion
```bash
curl -X POST https://YOUR_API_URL/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "index"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Document ingestion started successfully",
  "job_id": "job-456def",
  "status": "IN_PROGRESS"
}
```

## Check Ingestion Status
```bash
curl -X POST https://YOUR_API_URL/rag \
  -H "Content-Type: application/json" \
  -d '{
    "action": "status"
  }'
```

Response:
```json
{
  "success": true,
  "job_id": "job-456def",
  "status": "COMPLETE",
  "message": "Ingestion completed successfully",
  "documents": {
    "scanned": 25,
    "indexed": 25,
    "failed": 0
  }
}
```
