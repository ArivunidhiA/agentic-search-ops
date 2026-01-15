"""Production-grade agentic orchestration with Claude API integration."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.job import Job, JobState, JobEvent, JobStatus, JobType, JobEventType
from models.document import Document, DocumentStatus
from models.chunk import Chunk
from services.claude_client import ClaudeClient
from services.search import search_chunks
from core.prompts import (
    SUMMARIZATION_AGENT_PROMPT,
    SEARCH_AGENT_PROMPT,
    REFRESH_AGENT_PROMPT,
    SYNTHESIS_AGENT_PROMPT
)
from core.security import sanitize_text_input
from core.config import settings

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates long-running agentic workflows with:
    - State management (checkpointing)
    - Error recovery (retry logic)
    - Cost/time guardrails
    - Claude API integration
    """
    
    def __init__(self, job_id: str, db: AsyncSession):
        self.job_id = job_id
        self.db = db
        self.claude = ClaudeClient()
        self.start_time = datetime.utcnow()
        self.checkpoints: List[Dict] = []
    
    async def run(self):
        """Main entry point - routes to appropriate agent based on job type"""
        # Load job
        result = await self.db.execute(
            select(Job).where(Job.id == self.job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise Exception(f"Job {self.job_id} not found")
        
        # Load existing state if resuming
        existing_state = await self._load_latest_checkpoint()
        
        try:
            # Update status
            job.status = JobStatus.RUNNING
            if not job.started_at:
                job.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Create start event
            await self._create_event(JobEventType.START, {
                "message": "Job started",
                "resumed": existing_state is not None
            })
            
            # Route to appropriate agent
            if job.job_type == JobType.SUMMARIZATION:
                result = await self._run_summarization_agent(job, existing_state)
            elif job.job_type == JobType.DEEP_SEARCH:
                result = await self._run_search_agent(job, existing_state)
            elif job.job_type == JobType.REFRESH:
                result = await self._run_refresh_agent(job, existing_state)
            elif job.job_type == JobType.INGESTION:
                # Keep existing ingestion logic (not using Claude)
                result = await self._run_ingestion_job(job, existing_state)
            elif job.job_type == JobType.SEARCH:
                # Simple search (not deep search)
                result = await self._run_simple_search_job(job, existing_state)
            elif job.job_type == JobType.SYNTHESIS:
                result = await self._run_synthesis_job(job, existing_state)
            else:
                raise Exception(f"Unknown job type: {job.job_type}")
            
            # Success
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result
            await self.db.commit()
            
            await self._create_event(JobEventType.COMPLETE, {
                "message": "Job completed successfully",
                "stats": self.claude.get_stats()
            })
            
            logger.info(f"Job {self.job_id} completed successfully. Cost: ${self.claude.total_cost:.4f}")
            
        except Exception as e:
            # Failure - save state for recovery
            logger.error(f"Job {self.job_id} failed: {str(e)}", exc_info=True)
            
            result = await self.db.execute(
                select(Job).where(Job.id == self.job_id)
            )
            job = result.scalar_one_or_none()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                await self.db.commit()
            
            await self._create_event(JobEventType.ERROR, {
                "error": str(e),
                "stats": self.claude.get_stats()
            })
            raise
    
    async def _run_summarization_agent(
        self, 
        job: Job, 
        existing_state: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Summarizes multiple documents using Claude.
        
        Steps:
        1. Load documents to summarize
        2. For each document:
           a. Load chunks
           b. Call Claude to summarize
           c. Store summary
           d. Checkpoint
        3. Generate final synthesis
        """
        config = job.config or {}
        document_ids = config.get("document_ids", [])
        
        if not document_ids:
            # Summarize all completed documents (limit to 10)
            result = await self.db.execute(
                select(Document)
                .where(Document.status == DocumentStatus.COMPLETED)
                .limit(10)
            )
            documents = result.scalars().all()
            document_ids = [str(doc.id) for doc in documents]
        
        if not document_ids:
            raise Exception("No documents found to summarize")
        
        # Resume from checkpoint if exists
        start_index = 0
        summaries = []
        if existing_state:
            start_index = existing_state.get("processed_count", 0)
            summaries = existing_state.get("summaries", [])
            await self._create_event(JobEventType.RESUME, {
                "message": f"Resuming from document {start_index}/{len(document_ids)}"
            })
        
        # Process each document
        for i in range(start_index, len(document_ids)):
            # Check time limit
            elapsed = (datetime.utcnow() - self.start_time).total_seconds() / 60
            max_runtime = config.get("max_runtime_minutes", settings.MAX_JOB_RUNTIME_MINUTES)
            if elapsed > max_runtime:
                raise Exception(f"Time limit reached: {elapsed:.1f} minutes > {max_runtime} minutes")
            
            # Check cost limit
            if self.claude.total_cost >= config.get("max_cost_usd", settings.MAX_JOB_COST_USD):
                raise Exception(f"Cost limit reached: ${self.claude.total_cost:.4f}")
            
            doc_id = document_ids[i]
            
            # Load document
            doc_result = await self.db.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = doc_result.scalar_one_or_none()
            if not doc:
                logger.warning(f"Document {doc_id} not found, skipping")
                continue
            
            # Load document chunks
            chunk_result = await self.db.execute(
                select(Chunk)
                .where(Chunk.document_id == doc_id)
                .order_by(Chunk.chunk_index)
            )
            chunks = chunk_result.scalars().all()
            
            if not chunks:
                logger.warning(f"Document {doc_id} has no chunks, skipping")
                continue
            
            # Combine chunks (limit to 10000 chars to avoid token limits)
            full_text = "\n\n".join([c.content for c in chunks])
            if len(full_text) > 10000:
                full_text = full_text[:10000] + "... [truncated]"
            
            # Sanitize text before sending to Claude
            full_text = sanitize_text_input(full_text, max_length=10000)
            
            # Call Claude for summary
            logger.info(f"Summarizing document {i+1}/{len(document_ids)}: {doc.filename}")
            response = await self.claude.call(
                messages=[
                    {
                        "role": "user",
                        "content": f"Summarize the following document:\n\n{full_text}"
                    }
                ],
                system=SUMMARIZATION_AGENT_PROMPT,
                max_tokens=2000,
                model=settings.CLAUDE_MODEL,
                temperature=settings.CLAUDE_TEMPERATURE
            )
            
            # Store summary
            summary = {
                "document_id": doc_id,
                "filename": doc.filename,
                "summary": response["content"],
                "cost": response["cost"],
                "tokens": response["usage"]
            }
            summaries.append(summary)
            
            # Checkpoint
            await self._create_checkpoint({
                "processed_count": i + 1,
                "total_count": len(document_ids),
                "summaries": summaries,
                "current_cost": self.claude.total_cost
            }, step_name=f"summarize_doc_{i+1}")
            
            await self._create_event(JobEventType.CHECKPOINT, {
                "message": f"Completed document {i+1}/{len(document_ids)}",
                "document_id": doc_id,
                "filename": doc.filename,
                "cost": response["cost"]
            })
        
        # Final synthesis (combine all summaries)
        if len(summaries) > 1:
            logger.info("Synthesizing multiple summaries into overview")
            combined = "\n\n---\n\n".join([
                f"Document: {s['filename']}\n\n{s['summary']}" 
                for s in summaries
            ])
            
            # Limit combined text
            if len(combined) > 15000:
                combined = combined[:15000] + "... [truncated]"
            
            synthesis = await self.claude.call(
                messages=[
                    {
                        "role": "user",
                        "content": f"Synthesize these document summaries into a single overview:\n\n{combined}"
                    }
                ],
                system=SYNTHESIS_AGENT_PROMPT,
                max_tokens=3000,
                model=settings.CLAUDE_MODEL,
                temperature=settings.CLAUDE_TEMPERATURE
            )
            
            return {
                "individual_summaries": summaries,
                "synthesis": synthesis["content"],
                "total_documents": len(summaries),
                "total_cost": round(self.claude.total_cost, 4),
                "total_tokens": self.claude.total_tokens,
                "stats": self.claude.get_stats()
            }
        else:
            return {
                "summaries": summaries,
                "total_cost": round(self.claude.total_cost, 4),
                "total_tokens": self.claude.total_tokens,
                "stats": self.claude.get_stats()
            }
    
    async def _run_search_agent(
        self, 
        job: Job, 
        existing_state: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Deep search: decompose query, search KB, synthesize results.
        
        Steps:
        1. Decompose complex query into sub-queries (using Claude)
        2. Search KB for each sub-query
        3. Synthesize results (using Claude)
        """
        config = job.config or {}
        query = config.get("query", "")
        
        if not query:
            raise Exception("No query provided")
        
        # Sanitize query
        query = sanitize_text_input(query, max_length=500)
        
        # Step 1: Decompose query
        if existing_state and "sub_queries" in existing_state:
            sub_queries = existing_state["sub_queries"]
            await self._create_event(JobEventType.RESUME, {
                "message": "Resuming with existing sub-queries"
            })
        else:
            logger.info(f"Decomposing query: {query}")
            decompose_response = await self.claude.call(
                messages=[
                    {
                        "role": "user",
                        "content": f"Break down this complex query into 2-5 specific sub-queries that can be searched independently:\n\n{query}\n\nReturn only the sub-queries, one per line. Do not include numbers or bullets."
                    }
                ],
                system=SEARCH_AGENT_PROMPT,
                max_tokens=500,
                model=settings.CLAUDE_MODEL,
                temperature=settings.CLAUDE_TEMPERATURE
            )
            
            # Parse sub-queries (one per line)
            sub_queries = [
                q.strip() 
                for q in decompose_response["content"].split("\n") 
                if q.strip() and not q.strip().startswith("#") and len(q.strip()) > 5
            ]
            
            # Limit to 5 sub-queries
            sub_queries = sub_queries[:5]
            
            if not sub_queries:
                raise Exception("Failed to decompose query into sub-queries")
            
            await self._create_checkpoint({
                "sub_queries": sub_queries,
                "original_query": query
            }, step_name="decompose_query")
            
            await self._create_event(JobEventType.CHECKPOINT, {
                "message": f"Decomposed query into {len(sub_queries)} sub-queries",
                "sub_queries": sub_queries
            })
        
        # Step 2: Search for each sub-query
        all_results = []
        for i, sub_query in enumerate(sub_queries):
            # Check limits
            elapsed = (datetime.utcnow() - self.start_time).total_seconds() / 60
            max_runtime = config.get("max_runtime_minutes", settings.MAX_JOB_RUNTIME_MINUTES)
            if elapsed > max_runtime:
                raise Exception(f"Time limit reached: {elapsed:.1f} minutes")
            
            if self.claude.total_cost >= config.get("max_cost_usd", settings.MAX_JOB_COST_USD):
                raise Exception(f"Cost limit reached: ${self.claude.total_cost:.4f}")
            
            logger.info(f"Searching sub-query {i+1}/{len(sub_queries)}: {sub_query}")
            search_results = await search_chunks(
                sub_query,
                limit=5,
                document_ids=None,
                db=self.db
            )
            
            all_results.append({
                "sub_query": sub_query,
                "results": [
                    {
                        "chunk_id": r["chunk_id"],
                        "document_id": r["document_id"],
                        "content": r["content"][:500],  # Limit content length
                        "score": r["score"],
                        "document_metadata": r["document_metadata"]
                    }
                    for r in search_results
                ]
            })
            
            await self._create_checkpoint({
                "sub_queries": sub_queries,
                "results_gathered": i + 1,
                "all_results": all_results
            }, step_name=f"search_{i+1}")
        
        # Step 3: Synthesize
        logger.info("Synthesizing search results")
        context = "\n\n".join([
            f"Sub-query: {r['sub_query']}\nResults:\n" + 
            "\n".join([
                f"- {res['content']}... [Source: {res['document_metadata']['filename']}]" 
                for res in r['results']
            ])
            for r in all_results
        ])
        
        # Limit context size
        if len(context) > 12000:
            context = context[:12000] + "... [truncated]"
        
        synthesis = await self.claude.call(
            messages=[
                {
                    "role": "user",
                    "content": f"Original query: {query}\n\nSearch results:\n{context}\n\nProvide a comprehensive answer with source citations."
                }
            ],
            system=SEARCH_AGENT_PROMPT,
            max_tokens=4000,
            model=settings.CLAUDE_MODEL,
            temperature=settings.CLAUDE_TEMPERATURE
        )
        
        return {
            "query": query,
            "sub_queries": sub_queries,
            "search_results": all_results,
            "synthesis": synthesis["content"],
            "total_cost": round(self.claude.total_cost, 4),
            "total_tokens": self.claude.total_tokens,
            "stats": self.claude.get_stats()
        }
    
    async def _run_refresh_agent(
        self, 
        job: Job, 
        existing_state: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Reviews documents for accuracy and currency.
        
        Steps:
        1. Load documents
        2. For each document:
           a. Analyze with Claude
           b. Determine status (current/outdated/error)
           c. Flag for update if needed
        """
        config = job.config or {}
        max_documents = config.get("max_documents", 20)
        
        # Load documents (limit to recent ones or all if specified)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        result = await self.db.execute(
            select(Document)
            .where(Document.status == DocumentStatus.COMPLETED)
            .where(Document.upload_timestamp < cutoff_date)
            .limit(max_documents)
        )
        documents = result.scalars().all()
        
        if not documents:
            return {
                "message": "No documents found to review",
                "reviews": [],
                "total_cost": 0.0
            }
        
        # Resume from checkpoint
        start_index = 0
        reviews = []
        if existing_state:
            start_index = existing_state.get("processed", 0)
            reviews = existing_state.get("reviews", [])
        
        # Process each document
        for i in range(start_index, len(documents)):
            # Check limits
            elapsed = (datetime.utcnow() - self.start_time).total_seconds() / 60
            max_runtime = config.get("max_runtime_minutes", settings.MAX_JOB_RUNTIME_MINUTES)
            if elapsed > max_runtime:
                raise Exception(f"Time limit reached: {elapsed:.1f} minutes")
            
            if self.claude.total_cost >= config.get("max_cost_usd", settings.MAX_JOB_COST_USD):
                raise Exception(f"Cost limit reached: ${self.claude.total_cost:.4f}")
            
            doc = documents[i]
            
            # Load chunks (first 5 only for analysis)
            chunk_result = await self.db.execute(
                select(Chunk)
                .where(Chunk.document_id == doc.id)
                .order_by(Chunk.chunk_index)
                .limit(5)
            )
            chunks = chunk_result.scalars().all()
            
            if not chunks:
                continue
            
            sample_text = "\n".join([c.content for c in chunks])
            if len(sample_text) > 2000:
                sample_text = sample_text[:2000] + "... [truncated]"
            
            # Sanitize
            sample_text = sanitize_text_input(sample_text, max_length=2000)
            
            # Analyze
            logger.info(f"Reviewing document {i+1}/{len(documents)}: {doc.filename}")
            response = await self.claude.call(
                messages=[
                    {
                        "role": "user",
                        "content": f"Document: {doc.filename}\nUploaded: {doc.upload_timestamp}\n\nContent sample:\n{sample_text}\n\nAnalyze this document for currency and accuracy."
                    }
                ],
                system=REFRESH_AGENT_PROMPT,
                max_tokens=1500,
                model=settings.CLAUDE_MODEL,
                temperature=settings.CLAUDE_TEMPERATURE
            )
            
            reviews.append({
                "document_id": str(doc.id),
                "filename": doc.filename,
                "uploaded": doc.upload_timestamp.isoformat() if doc.upload_timestamp else None,
                "analysis": response["content"],
                "cost": response["cost"]
            })
            
            await self._create_checkpoint({
                "processed": i + 1,
                "total": len(documents),
                "reviews": reviews
            }, step_name=f"review_{i+1}")
        
        return {
            "documents_reviewed": len(reviews),
            "reviews": reviews,
            "total_cost": round(self.claude.total_cost, 4),
            "total_tokens": self.claude.total_tokens,
            "stats": self.claude.get_stats()
        }
    
    # Legacy job handlers (kept for compatibility)
    
    async def _run_ingestion_job(self, job: Job, existing_state: Optional[Dict]) -> Dict[str, Any]:
        """Run ingestion job (not using Claude - handled by ingest service)."""
        # This is handled by the ingest service, not here
        return {"message": "Ingestion handled by ingest service", "status": "completed"}
    
    async def _run_simple_search_job(self, job: Job, existing_state: Optional[Dict]) -> Dict[str, Any]:
        """Simple search job (not deep search)."""
        config = job.config or {}
        query = config.get("query", "")
        if not query:
            raise Exception("No query provided")
        
        query = sanitize_text_input(query, max_length=500)
        results = await search_chunks(query, limit=10, document_ids=None, db=self.db)
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
    
    async def _run_synthesis_job(self, job: Job, existing_state: Optional[Dict]) -> Dict[str, Any]:
        """Synthesis job - combine multiple summaries."""
        # Similar to summarization but for pre-existing summaries
        return {"message": "Synthesis job", "status": "completed"}
    
    # Helper methods
    
    async def _create_checkpoint(self, state_data: Dict, step_name: str):
        """Create a job state checkpoint"""
        checkpoint = JobState(
            job_id=self.job_id,
            state_data=state_data,
            step_name=step_name,
            checkpoint_timestamp=datetime.utcnow()
        )
        self.db.add(checkpoint)
        await self.db.commit()
        self.checkpoints.append(state_data)
        logger.debug(f"Checkpoint created: {step_name}")
    
    async def _load_latest_checkpoint(self) -> Optional[Dict]:
        """Load most recent checkpoint for resumption"""
        result = await self.db.execute(
            select(JobState)
            .where(JobState.job_id == self.job_id)
            .order_by(JobState.checkpoint_timestamp.desc())
            .limit(1)
        )
        checkpoint = result.scalar_one_or_none()
        if checkpoint:
            logger.info(f"Loaded checkpoint: {checkpoint.step_name}")
            return checkpoint.state_data
        return None
    
    async def _create_event(self, event_type: JobEventType, event_data: Dict):
        """Log a job event"""
        event = JobEvent(
            job_id=self.job_id,
            event_type=event_type,
            event_data=event_data,
            timestamp=datetime.utcnow()
        )
        self.db.add(event)
        await self.db.commit()
        logger.debug(f"Event created: {event_type.value}")


# Main function to run agent
async def run_agent_job(job_id: str, db: AsyncSession) -> None:
    """Entry point for agent job execution"""
    orchestrator = AgentOrchestrator(job_id, db)
    await orchestrator.run()
