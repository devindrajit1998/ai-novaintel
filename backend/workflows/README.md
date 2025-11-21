# Multi-Agent LangGraph Workflow

Complete multi-agent presales workflow using LangGraph for NovaIntel.

## Overview

The workflow orchestrates 6 specialized AI agents to transform RFP documents into comprehensive presales deliverables:

1. **RFP Analyzer** - Extracts summary, context, objectives, scope
2. **Challenge Extractor** - Identifies business/technical challenges
3. **Discovery Question Agent** - Generates categorized questions
4. **Value Proposition Agent** - Creates value propositions
5. **Case Study Matcher** - Matches relevant case studies
6. **Proposal Builder** - Drafts complete proposal

## Architecture

```
┌─────────────────┐
│  RFP Document   │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  RFP Analyzer       │ → Summary, Objectives, Scope
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Challenge Extractor │ → Business/Technical Challenges
└────────┬────────────┘
         │
         ├─────────────────┬─────────────────┐
         ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Discovery    │  │ Value Prop   │  │ Case Study   │
│ Question     │  │ Agent        │  │ Matcher      │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │ Proposal Builder │ → Complete Proposal Draft
              └──────────────────┘
```

## Workflow Execution

### State Management

The workflow maintains a global state (`WorkflowState`) that flows through all agents:

```python
{
    "project_id": int,
    "rfp_document_id": int,
    "rfp_text": str,
    "rfp_summary": str,
    "challenges": List[Dict],
    "discovery_questions": Dict[str, List[str]],
    "value_propositions": List[str],
    "matching_case_studies": List[Dict],
    "proposal_draft": Dict,
    "errors": List[str],
    "execution_log": List[Dict]
}
```

### Agent Details

#### 1. RFP Analyzer Agent
- **Input**: RFP text, retrieved context
- **Output**: Summary, context overview, business objectives, project scope
- **Model**: GPT-4-turbo-preview
- **Temperature**: 0.1 (factual)

#### 2. Challenge Extractor Agent
- **Input**: RFP summary, business objectives
- **Output**: List of challenges with type, impact, category
- **Model**: GPT-4-turbo-preview
- **Temperature**: 0.2

#### 3. Discovery Question Agent
- **Input**: Challenges
- **Output**: Categorized questions (Business, Technology, KPIs, Compliance)
- **Model**: GPT-4-turbo-preview
- **Temperature**: 0.3

#### 4. Value Proposition Agent
- **Input**: Challenges, RFP summary
- **Output**: List of value propositions
- **Model**: GPT-4-turbo-preview
- **Temperature**: 0.2

#### 5. Case Study Matcher Agent
- **Input**: Challenges
- **Output**: Matched case studies from database
- **Method**: Industry/keyword matching (can be enhanced with vector search)

#### 6. Proposal Builder Agent
- **Input**: RFP summary, challenges, value props, case studies
- **Output**: Complete proposal draft with all sections
- **Model**: GPT-4-turbo-preview
- **Temperature**: 0.2

## API Endpoints

### Run Complete Workflow
```http
POST /agents/run-all
Content-Type: application/json
Authorization: Bearer <token>

{
  "project_id": 1,
  "rfp_document_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "state_id": "1_123",
  "state": {
    "rfp_summary": "...",
    "challenges": [...],
    "discovery_questions": {...},
    "value_propositions": [...],
    "matching_case_studies": [...],
    "proposal_draft": {...}
  },
  "summary": {
    "challenges_count": 5,
    "value_propositions_count": 4,
    "case_studies_count": 3,
    "proposal_created": true
  }
}
```

### Get Workflow State
```http
POST /agents/get-state
Content-Type: application/json

{
  "state_id": "1_123"
}
```

### Debug Workflow
```http
GET /agents/debug?state_id=1_123
```

Returns detailed state information including errors and execution log.

## Usage Flow

### 1. Upload and Index RFP
```bash
# Upload RFP
POST /upload/rfp?project_id=1

# Build index
POST /rag/build-index
{"rfp_document_id": 123}
```

### 2. Run Workflow
```bash
POST /agents/run-all
{
  "project_id": 1,
  "rfp_document_id": 123
}
```

### 3. Access Results
- **Insights**: Automatically saved to database
- **Proposal**: Available in workflow state
- **State**: Queryable via `/agents/get-state`

## Error Handling

The workflow includes comprehensive error handling:

- **Missing Context**: Falls back to RFP text only
- **Agent Failures**: Errors logged in state, workflow continues
- **Database Errors**: Rolled back, errors returned
- **LLM Errors**: Captured and logged

All errors are stored in `state["errors"]` and `state["execution_log"]`.

## State Persistence

- **In-Memory**: Active states stored in `WorkflowManager`
- **Database**: Insights automatically saved to `Insights` table
- **State ID**: Format `{project_id}_{rfp_document_id}`

## Configuration

Requires OpenAI API key:
```env
OPENAI_API_KEY=your-key
```

## Performance

- **Execution Time**: ~30-60 seconds for full workflow
- **LLM Calls**: 5-6 API calls (one per agent)
- **Cost**: ~$0.10-0.20 per workflow run (GPT-4-turbo)

## Future Enhancements

1. **Async Execution**: Run agents in parallel where possible
2. **Streaming**: Stream agent outputs in real-time
3. **Caching**: Cache agent results for similar RFPs
4. **Vector Search**: Enhance case study matching with embeddings
5. **Human-in-the-Loop**: Add approval steps between agents
6. **Retry Logic**: Automatic retry for failed agents
7. **State Persistence**: Save state to database for recovery

## Testing

```bash
# 1. Upload RFP
curl -X POST "http://localhost:8000/upload/rfp?project_id=1" \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@sample_rfp.pdf"

# 2. Build index
curl -X POST "http://localhost:8000/rag/build-index" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rfp_document_id": 1}'

# 3. Run workflow
curl -X POST "http://localhost:8000/agents/run-all" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 1, "rfp_document_id": 1}'

# 4. Get state
curl -X POST "http://localhost:8000/agents/get-state" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"state_id": "1_1"}'
```

