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
    },
    {
        "filename": "docker_containers.txt",
        "content": """Docker and Containerization

Docker is a platform for developing, shipping, and running applications using containerization. Containers package an application with all its dependencies, ensuring it runs consistently across different environments.

Key concepts:
- Images: Read-only templates for creating containers
- Containers: Running instances of images
- Dockerfile: Instructions for building images
- Docker Compose: Tool for defining multi-container applications

Benefits of containerization:
- Consistency across development, testing, and production
- Isolation of applications and dependencies
- Resource efficiency compared to virtual machines
- Easy scaling and deployment
- Version control for application environments

Docker uses Linux kernel features like namespaces and cgroups to provide isolation. Popular container orchestration platforms include Kubernetes, Docker Swarm, and Amazon ECS.

Best practices include:
- Using multi-stage builds to reduce image size
- Not running containers as root
- Using specific version tags instead of 'latest'
- Implementing health checks
- Optimizing layer caching""",
        "file_size": 2048
    },
    {
        "filename": "api_design.txt",
        "content": """RESTful API Design Principles

REST (Representational State Transfer) is an architectural style for designing networked applications. RESTful APIs use HTTP methods to perform operations on resources.

Core principles:
1. Stateless: Each request contains all information needed
2. Client-Server: Separation of concerns
3. Uniform Interface: Consistent resource identification
4. Cacheable: Responses can be cached
5. Layered System: Architecture can have multiple layers

HTTP methods:
- GET: Retrieve resources
- POST: Create new resources
- PUT: Update entire resources
- PATCH: Partial updates
- DELETE: Remove resources

Status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Server Error

API versioning strategies include URL versioning (/api/v1/), header versioning, and query parameter versioning. Authentication methods include API keys, OAuth 2.0, and JWT tokens.

Best practices:
- Use nouns for resource names
- Implement pagination for large datasets
- Provide clear error messages
- Document APIs thoroughly
- Implement rate limiting
- Use HTTPS for security""",
        "file_size": 2304
    },
    {
        "filename": "git_version_control.txt",
        "content": """Git Version Control System

Git is a distributed version control system designed to handle everything from small to very large projects with speed and efficiency. Created by Linus Torvalds in 2005, Git has become the standard for version control.

Key concepts:
- Repository: Storage location for project files and history
- Commit: Snapshot of changes at a point in time
- Branch: Parallel version of the codebase
- Merge: Combining changes from different branches
- Remote: Reference to another repository

Common Git commands:
- git init: Initialize a new repository
- git add: Stage changes for commit
- git commit: Save changes to repository
- git push: Upload changes to remote
- git pull: Download and merge changes
- git branch: Manage branches
- git merge: Combine branches

Workflow strategies:
- Feature branches for new functionality
- Pull requests for code review
- Semantic versioning for releases
- Git flow or GitHub flow methodologies

Best practices:
- Write clear commit messages
- Commit frequently with logical units
- Use branches for features and fixes
- Keep main branch stable
- Review code before merging
- Use .gitignore for unnecessary files""",
        "file_size": 2560
    },
    {
        "filename": "security_best_practices.txt",
        "content": """Cybersecurity Best Practices

Security is crucial in modern software development. Protecting applications, data, and users requires a comprehensive approach covering multiple layers.

Authentication and Authorization:
- Implement strong password policies
- Use multi-factor authentication (MFA)
- Implement role-based access control (RBAC)
- Use OAuth 2.0 or JWT for API authentication
- Never store passwords in plain text

Data Protection:
- Encrypt sensitive data at rest and in transit
- Use HTTPS/TLS for all communications
- Implement proper input validation
- Sanitize user inputs to prevent injection attacks
- Use parameterized queries for databases

Common vulnerabilities to prevent:
- SQL Injection: Use prepared statements
- Cross-Site Scripting (XSS): Sanitize outputs
- Cross-Site Request Forgery (CSRF): Use tokens
- Insecure Direct Object References: Validate access
- Security Misconfiguration: Keep systems updated

Security practices:
- Regular security audits and penetration testing
- Keep dependencies updated
- Implement logging and monitoring
- Use security headers (CSP, HSTS, X-Frame-Options)
- Follow principle of least privilege
- Implement rate limiting and DDoS protection""",
        "file_size": 2816
    },
    {
        "filename": "microservices_architecture.txt",
        "content": """Microservices Architecture

Microservices architecture is an approach to building applications as a collection of small, independent services that communicate over well-defined APIs. Each service is responsible for a specific business function.

Key characteristics:
- Service independence: Services can be developed and deployed independently
- Technology diversity: Each service can use different technologies
- Fault isolation: Failure in one service doesn't crash the entire system
- Scalability: Services can scale independently based on demand
- Team autonomy: Small teams can own entire services

Benefits:
- Faster development and deployment
- Better fault tolerance
- Technology flexibility
- Easier to understand and maintain individual services
- Independent scaling

Challenges:
- Service communication complexity
- Data consistency across services
- Distributed system debugging
- Network latency
- Service discovery and configuration management

Common patterns:
- API Gateway: Single entry point for clients
- Service Mesh: Infrastructure layer for service communication
- Event-driven architecture: Services communicate via events
- Circuit Breaker: Prevent cascading failures
- Saga pattern: Manage distributed transactions

Tools and technologies:
- Kubernetes for orchestration
- Docker for containerization
- Service mesh (Istio, Linkerd)
- Message queues (RabbitMQ, Kafka)
- API gateways (Kong, AWS API Gateway)""",
        "file_size": 3328
    },
    {
        "filename": "testing_strategies.txt",
        "content": """Software Testing Strategies

Testing is a critical part of software development that ensures quality, reliability, and functionality of applications. A comprehensive testing strategy includes multiple levels and types of tests.

Testing levels:
1. Unit Testing: Test individual components in isolation
2. Integration Testing: Test interactions between components
3. System Testing: Test complete system functionality
4. Acceptance Testing: Validate against business requirements

Testing types:
- Functional Testing: Verify features work as specified
- Performance Testing: Check speed, responsiveness, stability
- Security Testing: Identify vulnerabilities
- Usability Testing: Evaluate user experience
- Regression Testing: Ensure changes don't break existing features

Test-driven development (TDD):
- Write tests before implementation
- Red-Green-Refactor cycle
- Ensures code meets requirements
- Improves code design

Testing best practices:
- Write clear, descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Keep tests independent and isolated
- Test edge cases and error conditions
- Maintain high code coverage
- Automate testing in CI/CD pipelines

Popular testing frameworks:
- Jest, Mocha for JavaScript
- pytest for Python
- JUnit for Java
- RSpec for Ruby
- xUnit for .NET

Continuous testing in CI/CD ensures code quality at every stage of development, catching issues early and reducing technical debt.""",
        "file_size": 2560
    },
    {
        "filename": "data_structures.txt",
        "content": """Data Structures and Algorithms

Data structures are ways of organizing and storing data in computer memory. Understanding data structures is fundamental to writing efficient algorithms and solving complex problems.

Common data structures:
- Arrays: Contiguous memory locations for elements
- Linked Lists: Nodes connected by pointers
- Stacks: LIFO (Last In First Out) structure
- Queues: FIFO (First In First Out) structure
- Trees: Hierarchical data organization
- Graphs: Nodes connected by edges
- Hash Tables: Key-value pairs with fast lookup

Algorithm complexity:
- Time Complexity: How execution time grows with input size
- Space Complexity: How memory usage grows with input size
- Big O notation: Describes worst-case performance
- Common complexities: O(1), O(log n), O(n), O(n log n), O(n²)

Sorting algorithms:
- Quick Sort: Divide and conquer, average O(n log n)
- Merge Sort: Divide and conquer, stable, O(n log n)
- Bubble Sort: Simple but slow, O(n²)
- Heap Sort: Uses heap data structure, O(n log n)

Searching algorithms:
- Binary Search: O(log n) for sorted arrays
- Linear Search: O(n) for unsorted arrays
- Hash-based search: O(1) average case

Choosing the right data structure depends on:
- Access patterns (read vs write frequency)
- Data relationships
- Memory constraints
- Performance requirements
- Implementation complexity""",
        "file_size": 2304
    },
    {
        "filename": "devops_practices.txt",
        "content": """DevOps Practices and CI/CD

DevOps is a set of practices that combines software development (Dev) and IT operations (Ops) to shorten the development lifecycle and provide continuous delivery with high quality.

Core principles:
- Collaboration between development and operations
- Automation of processes
- Continuous integration and deployment
- Infrastructure as code
- Monitoring and logging

CI/CD Pipeline:
- Continuous Integration: Automatically test code changes
- Continuous Deployment: Automatically deploy to production
- Continuous Delivery: Ready for deployment at any time

Key practices:
- Version control for all code and configurations
- Automated testing at multiple levels
- Infrastructure as code (Terraform, CloudFormation)
- Configuration management (Ansible, Puppet, Chef)
- Containerization and orchestration
- Monitoring and alerting
- Log aggregation and analysis

Benefits:
- Faster time to market
- Reduced deployment failures
- Improved collaboration
- Better quality and reliability
- Increased efficiency

Tools:
- CI/CD: Jenkins, GitLab CI, GitHub Actions, CircleCI
- Configuration: Ansible, Terraform, Kubernetes
- Monitoring: Prometheus, Grafana, ELK Stack
- Container: Docker, Kubernetes, Docker Swarm

DevOps culture emphasizes:
- Shared responsibility
- Fast feedback loops
- Continuous improvement
- Learning from failures
- Automation over manual processes""",
        "file_size": 2816
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
