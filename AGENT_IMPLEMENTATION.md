# Agentic Orchestration Implementation

## Overview

Production-grade agentic orchestration with real Claude API integration, state management, and error recovery has been implemented.

## Files Created/Modified

### New Files:
1. **`backend/services/claude_client.py`** - Safe Claude API wrapper
   - Cost tracking and limits
   - Rate limiting (1 req/sec minimum)
   - Retry logic with exponential backoff
   - Timeout protection (60s default)
   - Token counting and pricing

2. **`backend/core/prompts.py`** - System prompts for agents
   - `SUMMARIZATION_AGENT_PROMPT` - Document summarization
   - `SEARCH_AGENT_PROMPT` - Query decomposition and synthesis
   - `REFRESH_AGENT_PROMPT` - Document validation
   - `SYNTHESIS_AGENT_PROMPT` - Multi-document synthesis

### Modified Files:
1. **`backend/services/agent.py`** - Complete rewrite
   - `AgentOrchestrator` class with full state management
   - Three real agents: summarization, deep_search, refresh
   - Checkpointing for pause/resume
   - Cost and time guardrails
   - Error recovery

2. **`backend/models/job.py`** - Added job types
   - `SUMMARIZATION` - Document summarization job
   - `DEEP_SEARCH` - Multi-step search with synthesis

3. **`backend/core/config.py`** - Added Claude settings
   - `CLAUDE_MODEL` - Model identifier
   - `CLAUDE_MAX_TOKENS` - Max tokens per request
   - `CLAUDE_TEMPERATURE` - Sampling temperature

4. **`requirements.txt`** - Added dependency
   - `anthropic>=0.39.0`

## Agent Implementations

### 1. Summarization Agent (`_run_summarization_agent`)

**Purpose**: Summarize multiple documents using Claude

**Steps**:
1. Load documents (from config or all completed documents)
2. For each document:
   - Load chunks
   - Combine text (limit 10k chars)
   - Call Claude with `SUMMARIZATION_AGENT_PROMPT`
   - Store summary with cost tracking
   - Create checkpoint
3. If multiple documents, synthesize into overview

**Checkpoints**: After each document summary
**Cost Tracking**: Per-document and total
**Resume**: Can resume from any document index

### 2. Deep Search Agent (`_run_search_agent`)

**Purpose**: Decompose complex queries, search KB, synthesize results

**Steps**:
1. Decompose query into 2-5 sub-queries (Claude)
2. Search KB for each sub-query
3. Synthesize all results into comprehensive answer (Claude)

**Checkpoints**: After decomposition, after each search, before synthesis
**Cost Tracking**: Per Claude call
**Resume**: Can resume from any sub-query

### 3. Refresh Agent (`_run_refresh_agent`)

**Purpose**: Review documents for accuracy and currency

**Steps**:
1. Load documents older than 90 days
2. For each document:
   - Load sample chunks (first 5)
   - Analyze with Claude using `REFRESH_AGENT_PROMPT`
   - Determine status (CURRENT/OUTDATED/INCOMPLETE/ERROR)
   - Create checkpoint

**Checkpoints**: After each document review
**Cost Tracking**: Per document analysis
**Resume**: Can resume from any document index

## Security Features

✅ **No Code Execution**: Claude responses are never executed as code
✅ **Input Sanitization**: All inputs sanitized before sending to Claude
✅ **Cost Limits**: Enforced at multiple levels (per-request, per-job, global)
✅ **Time Limits**: Runtime limits enforced with checks
✅ **Rate Limiting**: 1 request per second minimum
✅ **Token Limits**: Max tokens per request enforced
✅ **Error Handling**: All errors caught and logged
✅ **Audit Logging**: All Claude interactions logged as JobEvents

## Cost Tracking

- **Input tokens**: $3 per MTok
- **Output tokens**: $15 per MTok
- **Per-request tracking**: Each API call tracked
- **Per-job tracking**: Total cost per job
- **Limit enforcement**: Stops when limit reached

## Checkpointing

- **State persistence**: All state saved to `JobState` table
- **Resume capability**: Jobs can resume from last checkpoint
- **Step tracking**: Each checkpoint includes step name
- **Data structure**: JSON state data for flexibility

## Error Recovery

- **Retry logic**: 3 attempts with exponential backoff
- **Rate limit handling**: Special handling for 429 errors
- **Timeout protection**: 60s timeout per request
- **State preservation**: Failed jobs save state for recovery
- **Graceful degradation**: Errors logged, job marked as failed

## Usage Example

```python
# Create a summarization job
POST /api/v1/jobs
{
  "job_type": "summarization",
  "config": {
    "document_ids": ["doc1", "doc2"],
    "max_runtime_minutes": 60,
    "max_cost_usd": 2.0
  }
}

# Job will:
# 1. Load documents
# 2. Summarize each with Claude
# 3. Create checkpoints
# 4. Synthesize if multiple documents
# 5. Store results in job.result
```

## Testing Checklist

- [ ] Summarization agent with 3 documents
- [ ] Deep search with complex query
- [ ] Refresh agent on old documents
- [ ] Cost limit enforcement (set max_cost=0.10)
- [ ] Time limit enforcement (set max_runtime=2)
- [ ] Resume from checkpoint (pause and resume)
- [ ] Error recovery (artificial failure)
- [ ] Rate limiting (multiple rapid requests)
- [ ] Token counting accuracy
- [ ] Checkpoint data integrity

## Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
MAX_JOB_COST_USD=5.0
MAX_JOB_RUNTIME_MINUTES=120
CLAUDE_MODEL=claude-sonnet-4-20250514
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=1.0
```

## Next Steps

1. Test with real Claude API key
2. Verify cost tracking accuracy
3. Test checkpoint resume functionality
4. Monitor job execution logs
5. Adjust prompts based on results
6. Add more agent types as needed
