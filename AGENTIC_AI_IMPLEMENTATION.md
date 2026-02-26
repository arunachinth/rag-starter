# Agentic AI Implementation in RAG Starter Project

## Executive Summary

This project implements a **multi-agent orchestration system** for Retrieval-Augmented Generation (RAG) using Amazon Bedrock. The architecture employs **5 specialized AI agents** working in a coordinated pipeline to provide contextual, accurate, and validated responses to user queries about policy documents.

---

## Agentic AI Architecture

### What is Agentic AI?

Agentic AI refers to autonomous AI systems that can:
- Make decisions independently
- Break down complex tasks into subtasks
- Coordinate multiple specialized components
- Maintain state and context across interactions
- Self-validate and improve outputs

### Our Implementation

We built a **custom multi-agent orchestration system** (not using AWS Bedrock Agents service) where each agent has a specific role and responsibility.

---

## The 5 Specialized Agents

### 1. **Entity Extractor Agent**
- **Model**: Claude 3 Haiku (fast, cost-effective)
- **Purpose**: Extract structured user context from natural language queries
- **Extracts**:
  - Department (e.g., police, fire, HR)
  - Years of service
  - State and county
  - Policy type
- **Intelligence**: Preserves existing entities across sessions, only updates when new information is provided
- **Example**: 
  - Input: "I'm a police officer in California with 15 years"
  - Output: `{"department": "police", "state": "California", "years_of_service": 15}`

### 2. **Query Enhancer Agent**
- **Model**: Claude 3 Haiku
- **Purpose**: Enrich user queries with contextual information for better retrieval
- **Uses**:
  - Extracted entities from current session
  - Last 2 conversation turns from history
  - User profile information
- **Intelligence**: Rewrites vague queries into specific, context-aware search queries
- **Example**:
  - Original: "What's my vacation policy?"
  - Enhanced: "What is the vacation policy for police officers in California with 15 years of service?"

### 3. **Retrieval Agent**
- **Service**: Bedrock Agent Runtime (Knowledge Base API)
- **Purpose**: Fetch the most relevant documents from the vector database
- **Configuration**:
  - Vector search with top 5 results
  - Semantic similarity scoring
  - Returns content, source, and relevance score
- **Intelligence**: Uses the enhanced query (not the original) for better semantic matching

### 4. **Response Generator Agent**
- **Model**: Claude 3 Sonnet (balanced performance and quality)
- **Purpose**: Generate contextual, personalized answers with citations
- **Inputs**:
  - Original user query
  - User profile (entities)
  - Retrieved documents (top 3)
  - Recent conversation history (last 2 turns)
- **Intelligence**: 
  - Personalizes responses based on user profile
  - Cites specific sources
  - Acknowledges conversation context
  - States when information is missing

### 5. **Validation Agent**
- **Model**: Claude 3 Sonnet
- **Purpose**: Fact-check the generated response against source documents
- **Validates**:
  - Claims are supported by documents
  - No hallucinations or fabricated information
  - Numerical accuracy (dates, numbers, percentages)
  - No contradictions with source material
- **Output**:
  - `is_valid`: boolean
  - `confidence`: 0.0-1.0 score
  - `issues`: list of problems found
  - `supported_claims`: verified statements
  - `unsupported_claims`: unverified statements
- **Intelligence**: Acts as a quality gate to prevent misinformation

---

## Orchestration Flow

The **OrchestratorAgent** coordinates all 5 agents in a sequential pipeline:

```
User Query
    ↓
1. Entity Extractor → Extract user context
    ↓
2. Query Enhancer → Enrich query with context
    ↓
3. Retrieval Agent → Fetch relevant documents
    ↓
4. Response Generator → Create personalized answer
    ↓
5. Validation Agent → Verify accuracy
    ↓
6. Conversation Memory → Save state
    ↓
Return Response
```

---

## Conversation Memory System

### Purpose
Maintains stateful context across multiple interactions within a session.

### Storage
- **Service**: Amazon DynamoDB
- **Table**: rag-conversation-memory
- **Key**: session_id

### Stored Data
- **Entities**: User profile accumulated over conversation
- **History**: Last 10 query-response pairs
- **Timestamp**: Last update time

### Intelligence
- Entities persist and accumulate (user doesn't repeat information)
- History provides context for follow-up questions
- Enables multi-turn conversations with memory

---

## Agentic AI Characteristics Demonstrated

### ✅ Autonomy
Each agent makes independent decisions within its domain:
- Entity Extractor decides what to extract and preserve
- Query Enhancer decides how to rewrite queries
- Validation Agent decides if response is accurate

### ✅ Specialization
Each agent is optimized for a specific task:
- Haiku for fast extraction/enhancement (cost-effective)
- Sonnet for quality generation/validation (higher accuracy)

### ✅ Coordination
Orchestrator manages the pipeline:
- Sequential execution with data passing
- Error handling at each stage
- Fallback mechanisms (e.g., use original query if enhancement fails)

### ✅ State Management
Conversation Memory provides persistence:
- Session-based context
- Entity accumulation
- History tracking

### ✅ Self-Validation
Validation Agent provides quality control:
- Checks for hallucinations
- Verifies factual accuracy
- Provides confidence scores

---

## Did We Use Strands?

**No, this project does not use Strands.**

### What We Used Instead:
- **Custom multi-agent orchestration** built in Python
- **Direct Bedrock API calls** (invoke_model, retrieve)
- **Manual agent coordination** through the OrchestratorAgent class
- **Custom conversation memory** with DynamoDB

### Strands vs. Our Approach:

| Feature | Strands | Our Implementation |
|---------|---------|-------------------|
| Agent Framework | Managed service | Custom Python classes |
| Orchestration | Built-in | Manual coordination |
| Memory | Managed | DynamoDB custom |
| Flexibility | Limited to framework | Full control |
| Complexity | Lower | Higher (more code) |

---

## Key Benefits of Our Agentic Approach

### 1. **Contextual Awareness**
- Remembers user profile across conversation
- Uses history for follow-up questions
- Personalizes responses

### 2. **Improved Retrieval**
- Enhanced queries lead to better document matching
- Semantic search with context yields more relevant results

### 3. **Quality Assurance**
- Validation agent prevents hallucinations
- Confidence scoring for transparency
- Source citations for verification

### 4. **Scalability**
- Each agent can be optimized independently
- Easy to add new agents (e.g., summarization, translation)
- Model selection per agent (cost vs. quality tradeoff)

### 5. **Transparency**
- Returns enhanced query, entities, validation results
- Shows which documents were used
- Provides confidence scores

---

## Technical Implementation Details

### Model Selection Strategy
- **Claude 3 Haiku**: Fast, cost-effective for extraction and enhancement
- **Claude 3 Sonnet**: Balanced quality for generation and validation
- **Rationale**: Optimize cost/performance per agent role

### API Calls
- **bedrock-runtime**: `invoke_model` for LLM calls (4 agents)
- **bedrock-agent-runtime**: `retrieve` for Knowledge Base (1 agent)
- **dynamodb**: `get_item`, `put_item` for memory

### Error Handling
- Try-catch blocks in each agent
- Fallback to defaults if agent fails
- Graceful degradation (e.g., use original query if enhancement fails)

### Performance
- **Lambda**: 1024MB, 300s timeout
- **Parallel potential**: Agents could run in parallel (not implemented)
- **Caching**: Conversation memory reduces redundant processing

---

## Comparison: Agentic vs. Traditional RAG

| Aspect | Traditional RAG | Our Agentic RAG |
|--------|----------------|-----------------|
| Query Processing | Direct query to vector DB | Enhanced with context |
| Personalization | None | User profile-based |
| Memory | Stateless | Stateful with DynamoDB |
| Validation | None | Automated fact-checking |
| Complexity | Simple pipeline | Multi-agent orchestration |
| Accuracy | Good | Better (validated) |
| Cost | Lower | Higher (more LLM calls) |

---

## Future Enhancements

### Potential Additional Agents
1. **Summarization Agent**: Condense long documents
2. **Translation Agent**: Multi-language support
3. **Routing Agent**: Direct queries to specialized knowledge bases
4. **Feedback Agent**: Learn from user corrections

### Optimization Opportunities
1. **Parallel Execution**: Run Entity Extractor and Query Enhancer in parallel
2. **Caching**: Cache enhanced queries for similar inputs
3. **Model Upgrades**: Use Claude 3.5 Sonnet for better quality
4. **Streaming**: Stream response generation for better UX

---

## Conclusion

This project demonstrates a **production-ready agentic AI system** that goes beyond simple RAG by:
- Implementing 5 specialized agents with distinct responsibilities
- Maintaining conversational context across sessions
- Validating outputs for accuracy and reliability
- Personalizing responses based on user profiles
- Providing transparency through enhanced queries and validation results

**We did NOT use Strands** - this is a custom-built multi-agent orchestration system using direct Bedrock API calls and manual coordination logic.

The architecture is **serverless, scalable, and cost-optimized** through strategic model selection (Haiku for speed, Sonnet for quality).
