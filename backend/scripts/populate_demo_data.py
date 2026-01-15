"""Script to populate database with demo data for testing."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from db.database import AsyncSessionLocal, init_db
from models.document import Document, DocumentStatus
from models.chunk import Chunk
from models.job import Job, JobStatus, JobType, JobEvent, JobEventType


# Demo documents content
DEMO_DOCUMENTS = [
    {
        "filename": "introduction_to_ai.txt",
        "content": """Introduction to Artificial Intelligence

Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines capable of performing tasks that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding.

Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed. Deep learning, a further subset, uses neural networks with multiple layers to analyze various factors of data.

AI applications are widespread, including:
- Natural language processing for chatbots and translation
- Computer vision for image recognition
- Autonomous vehicles
- Healthcare diagnostics
- Financial trading algorithms

The future of AI holds promise for solving complex problems in climate change, healthcare, and education.""",
        "file_size": 1024
    },
    {
        "filename": "python_basics.txt",
        "content": """Python Programming Basics

Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991.

Key features of Python:
- Easy to learn syntax
- Extensive standard library
- Cross-platform compatibility
- Strong community support
- Versatile applications (web, data science, AI, automation)

Python uses indentation to define code blocks, making it highly readable. Variables are dynamically typed, meaning you don't need to declare variable types.

Common data structures include lists, dictionaries, tuples, and sets. Python supports object-oriented, functional, and procedural programming paradigms.

Popular Python frameworks include Django and Flask for web development, NumPy and Pandas for data analysis, and TensorFlow and PyTorch for machine learning.""",
        "file_size": 1536
    },
    {
        "filename": "database_design.txt",
        "content": """Database Design Principles

Database design is the process of producing a detailed data model of a database. This model contains all the needed logical and physical design choices and physical storage parameters needed to generate a design.

Key principles:
1. Normalization: Organize data to minimize redundancy
2. Data integrity: Ensure accuracy and consistency
3. Performance: Optimize for query speed
4. Scalability: Design for growth
5. Security: Protect sensitive data

Relational databases use tables with rows and columns. Relationships between tables are established through foreign keys. Common database management systems include PostgreSQL, MySQL, SQLite, and Oracle.

NoSQL databases like MongoDB, Cassandra, and Redis offer alternative data models for specific use cases such as document storage, wide-column stores, and key-value pairs.

Indexing is crucial for query performance. Primary keys uniquely identify rows, while foreign keys maintain referential integrity between tables.""",
        "file_size": 2048
    },
    {
        "filename": "web_development.txt",
        "content": """Modern Web Development

Web development involves creating websites and web applications. It encompasses frontend (client-side) and backend (server-side) development.

Frontend technologies:
- HTML for structure
- CSS for styling
- JavaScript for interactivity
- React, Vue, Angular for modern frameworks

Backend technologies:
- Node.js, Python, Java, Go for server-side logic
- RESTful APIs and GraphQL for data exchange
- Databases for data storage
- Authentication and authorization systems

Full-stack development combines both frontend and backend skills. Modern web applications often use:
- Single Page Applications (SPAs)
- Progressive Web Apps (PWAs)
- Microservices architecture
- Containerization with Docker
- Cloud deployment on AWS, Azure, or GCP

Security is paramount, including HTTPS, input validation, SQL injection prevention, and XSS protection. Performance optimization involves caching, CDN usage, and code minification.""",
        "file_size": 2560
    },
    {
        "filename": "cloud_computing.txt",
        "content": """Cloud Computing Fundamentals

Cloud computing is the delivery of computing services including servers, storage, databases, networking, software, analytics, and intelligence over the Internet ("the cloud") to offer faster innovation, flexible resources, and economies of scale.

Service models:
1. Infrastructure as a Service (IaaS): Virtual machines, storage, networks
2. Platform as a Service (PaaS): Development platforms and tools
3. Software as a Service (SaaS): Complete applications

Deployment models:
- Public cloud: Services over the public internet
- Private cloud: Dedicated infrastructure
- Hybrid cloud: Combination of public and private

Major cloud providers include Amazon Web Services (AWS), Microsoft Azure, and Google Cloud Platform (GCP). Each offers extensive services for compute, storage, databases, machine learning, and more.

Benefits of cloud computing:
- Cost reduction through pay-as-you-go pricing
- Scalability and elasticity
- Global reach and availability
- Automatic software updates
- Disaster recovery and backup solutions

Cloud security involves shared responsibility models, encryption, identity and access management, and compliance with regulations like GDPR and HIPAA.""",
        "file_size": 3072
    }
]


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Simple text chunking with overlap."""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap  # Overlap for context
        
    return chunks


async def create_demo_documents(db: AsyncSession):
    """Create demo documents and chunks."""
    print("Creating demo documents...")
    
    for doc_data in DEMO_DOCUMENTS:
        # Create document
        document = Document(
            id=str(uuid4()),
            filename=doc_data["filename"],
            s3_key=f"documents/{doc_data['filename']}",
            upload_timestamp=datetime.utcnow(),
            file_size=doc_data["file_size"],
            content_type="text/plain",
            status=DocumentStatus.COMPLETED,
            metadata_json={"source": "demo", "created_by": "demo_script"}
        )
        db.add(document)
        await db.flush()  # Flush to get document ID
        
        # Create chunks
        chunks = chunk_text(doc_data["content"], chunk_size=1000, overlap=200)
        for idx, chunk_content in enumerate(chunks):
            chunk = Chunk(
                id=str(uuid4()),
                document_id=document.id,
                content=chunk_content,
                chunk_index=idx,
                token_count=len(chunk_content.split()),
                created_at=datetime.utcnow()
            )
            db.add(chunk)
        
        print(f"  ✓ Created {doc_data['filename']} with {len(chunks)} chunks")
    
    await db.commit()
    print(f"✓ Created {len(DEMO_DOCUMENTS)} documents")


async def create_demo_jobs(db: AsyncSession):
    """Create demo jobs."""
    print("Creating demo jobs...")
    
    # Get a document ID for job reference
    from sqlalchemy import select
    result = await db.execute(select(Document).limit(1))
    document = result.scalar_one_or_none()
    
    if not document:
        print("  ⚠ No documents found, skipping job creation")
        return
    
    # Create a completed summarization job
    job1 = Job(
        id=str(uuid4()),
        job_type=JobType.SUMMARIZATION,
        status=JobStatus.COMPLETED,
        config={"document_ids": [document.id], "max_cost": 1.0},
        result={"total_documents": 1, "total_cost": 0.15},
        created_at=datetime.utcnow() - timedelta(hours=2),
        started_at=datetime.utcnow() - timedelta(hours=2),
        completed_at=datetime.utcnow() - timedelta(hours=1, minutes=45)
    )
    db.add(job1)
    await db.flush()
    
    # Create events for job1
    events1 = [
        JobEvent(job_id=job1.id, event_type=JobEventType.START, event_data={"message": "Job started"}, timestamp=job1.started_at),
        JobEvent(job_id=job1.id, event_type=JobEventType.CHECKPOINT, event_data={"step": "processing_document"}, timestamp=job1.started_at + timedelta(minutes=5)),
        JobEvent(job_id=job1.id, event_type=JobEventType.COMPLETE, event_data={"message": "Job completed successfully"}, timestamp=job1.completed_at)
    ]
    for event in events1:
        db.add(event)
    
    # Create a running search job
    job2 = Job(
        id=str(uuid4()),
        job_type=JobType.DEEP_SEARCH,
        status=JobStatus.RUNNING,
        config={"query": "What are the key features of Python?", "max_cost": 0.50},
        created_at=datetime.utcnow() - timedelta(minutes=10),
        started_at=datetime.utcnow() - timedelta(minutes=10)
    )
    db.add(job2)
    await db.flush()
    
    # Create events for job2
    events2 = [
        JobEvent(job_id=job2.id, event_type=JobEventType.START, event_data={"message": "Job started"}, timestamp=job2.started_at),
        JobEvent(job_id=job2.id, event_type=JobEventType.CHECKPOINT, event_data={"step": "query_decomposition"}, timestamp=job2.started_at + timedelta(minutes=2))
    ]
    for event in events2:
        db.add(event)
    
    await db.commit()
    print(f"✓ Created 2 demo jobs")


async def main():
    """Main function to populate demo data."""
    print("=" * 60)
    print("Populating database with demo data...")
    print("=" * 60)
    
    # Initialize database
    await init_db()
    print("✓ Database initialized\n")
    
    # Create session
    async with AsyncSessionLocal() as db:
        try:
            # Create documents and chunks
            await create_demo_documents(db)
            print()
            
            # Create jobs
            await create_demo_jobs(db)
            print()
            
            print("=" * 60)
            print("✓ Demo data population complete!")
            print("=" * 60)
            print("\nYou can now:")
            print("  - View documents at http://localhost:5174/documents")
            print("  - Search content at http://localhost:5174/search")
            print("  - View jobs at http://localhost:5174/jobs")
            print("  - Check metrics at http://localhost:8001/api/v1/metrics")
            
        except Exception as e:
            await db.rollback()
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    from datetime import timedelta
    asyncio.run(main())
