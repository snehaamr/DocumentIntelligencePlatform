# 📄 AI Document Intelligence Platform

An AI-powered document processing platform built with **Django**, **Django REST Framework**, **Celery**, **Redis**, **PostgreSQL**, **Docker**, and **OpenAI**.

The platform allows authenticated users to upload documents, extract text, leverage Large Language Models (LLMs) to classify and summarize content, and process documents asynchronously using background workers.

The project follows production-oriented backend engineering practices including layered architecture, repository and service patterns, transactional consistency, asynchronous processing, containerized deployment, automated testing, and robust error handling.

---

# Features

## Authentication

* JWT-based authentication
* User registration and login
* Access token refresh
* User-specific document ownership
* Protected API endpoints

---

## Document Upload

Users can upload PDF, image, or text documents.

Each uploaded document stores:

* Original filename
* MIME type
* File size
* Upload timestamp
* Processing status
* Owner

---

## AI Document Processing

After upload, documents are processed asynchronously.

Processing pipeline:

```text
Upload
    ↓
Queue Celery Task
    ↓
Text Extraction
    ↓
OpenAI Analysis
    ↓
Classification
    ↓
Summary Generation
    ↓
Confidence Score
    ↓
Persist Results
```

The AI extracts structured information including:

* Document type
* Summary
* Confidence score
* Structured AI response

---

## Asynchronous Processing

Document processing is executed using **Celery** workers with **Redis** as the message broker.

Benefits include:

* Non-blocking uploads
* Faster API responses
* Horizontal scalability
* Fault isolation
* Automatic retry capability
* Separation of API and background workloads

---

## Processing History

Every processing attempt is recorded.

Each execution stores:

* Status
* Start time
* Completion time
* Processing duration
* Error message
* Model used
* Token usage (when available)

This provides complete auditability of document processing.

---

## Retry Failed Processing

Failed document processing can be retried without uploading the document again.

Retry workflow:

```text
FAILED
    ↓
Retry Endpoint
    ↓
Database Transaction
    ↓
Row Lock
    ↓
Queue Celery Task
    ↓
PROCESSING
    ↓
PROCESSED
```

Retries are only allowed for failed documents.

The implementation uses:

* `transaction.atomic()`
* `select_for_update()`
* `transaction.on_commit()`

to prevent duplicate processing and race conditions.

---

## Search and Filtering

Documents can be filtered by:

* Processing status
* Document type
* Confidence score
* Filename
* Summary text

Results are paginated for efficient retrieval.

---

# Architecture

The project follows a layered architecture that separates API logic, business logic, persistence, and background processing.

```text
                     Client
                        │
                        ▼
             Django REST Framework
                        │
                JWT Authentication
                        │
                        ▼
               Service Layer
              (Business Logic)
                        │
                        ▼
             Repository Layer
             (Database Access)
                        │
                        ▼
            PostgreSQL / SQLite
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
 Processing Logs                  Celery Queue
                                          │
                                          ▼
                                   Redis Broker
                                          │
                                          ▼
                                    Celery Worker
                                          │
                                          ▼
                                  Text Extraction
                                          │
                                          ▼
                                      OpenAI API
```

---

# Project Structure

```text
DocumentIntelligencePlatform/

├── apps/
│   ├── documents/
│   ├── users/
│   ├── feedback/
│   └── ai_engine/
│
├── repositories/
│   └── document_repository.py
│
├── services/
│   ├── document_service.py
│   ├── extraction_service.py
│   ├── ai_document_service.py
│   └── tasks.py
│
├── config/
│
├── media/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── manage.py
```

---

# Technology Stack

## Backend

* Python 3.13
* Django 6
* Django REST Framework

## Database

* SQLite (local development)
* PostgreSQL (Docker deployment)

## Authentication

* JWT Authentication

## Background Processing

* Celery
* Redis

## AI

* OpenAI Chat Completions API
* Pydantic

## Infrastructure

* Docker
* Docker Compose

## Testing

* Django Test Framework

---

# API Endpoints

## Authentication

```text
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
```

---

## Documents

```text
POST /api/documents/
GET  /api/documents/
GET  /api/documents/{id}/
POST /api/documents/{id}/retry/
GET  /api/documents/{id}/history/
```

---

# Processing Lifecycle

```text
UPLOADED
      │
      ▼
PROCESSING
      │
      ├──────────────► FAILED
      │                     │
      │                     ▼
      │               Retry Request
      │                     │
      ▼                     │
PROCESSED ◄─────────────────┘
```

---

# Running Locally

Create a virtual environment.

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Run database migrations.

```bash
python manage.py migrate
```

Start Redis.

```bash
redis-server
```

Start Celery.

```bash
celery -A config worker --loglevel=info
```

Run Django.

```bash
python manage.py runserver
```

---

# Running with Docker

Build the containers.

```bash
docker compose build
```

Start the complete application.

```bash
docker compose up
```

The following services start automatically:

* Django
* PostgreSQL
* Redis
* Celery Worker

---

# Running Tests

Run the complete test suite locally.

```bash
python manage.py test apps.documents.tests
```

Run tests inside Docker.

```bash
docker compose exec web python manage.py test apps.documents.tests
```

Current automated coverage includes:

* Repository layer
* Service layer
* API endpoints
* Authentication
* Authorization
* Retry workflow
* Processing history

**22 automated tests**

---

# Design Decisions

## Layered Architecture

The application separates presentation, business logic, persistence, and background processing into independent layers. This improves maintainability, testability, and separation of concerns.

---

## Repository Pattern

All database operations are isolated from business logic.

Advantages:

* Centralized data access
* Easier testing
* Cleaner services
* Better maintainability

---

## Service Layer

Business logic is separated from API controllers.

Responsibilities include:

* Validation
* Document orchestration
* AI integration
* Transaction management
* Retry logic
* Error handling

---

## Asynchronous Processing

Long-running AI operations execute in Celery workers.

Advantages:

* Improved response times
* Better scalability
* Fault isolation
* Background retries

---

## Transactional Retry

Retry operations use:

* `transaction.atomic()`
* `select_for_update()`
* `transaction.on_commit()`

to ensure that only one retry request can queue processing for a document at a time.

---

# Error Handling

Processing failures are recorded without crashing the application.

Each failed execution stores:

* Status
* Error message
* Processing duration

Failed documents remain available for retry without requiring another upload.

---

# Security

The platform includes several security mechanisms:

* JWT Authentication
* User-specific document ownership
* Protected API endpoints
* Transaction-safe retry operations
* Row-level locking
* Background task isolation

---

# Engineering Highlights

This project demonstrates several backend engineering concepts commonly used in production systems.

* RESTful API Design
* Layered Architecture
* Repository Pattern
* Service Layer Pattern
* Dependency Injection
* JWT Authentication
* Celery Background Processing
* Redis Message Broker
* PostgreSQL
* Docker Compose
* Transaction Management
* Row-Level Locking
* Asynchronous Processing
* Retry Mechanisms
* AI Integration
* Search and Filtering
* Pagination
* Automated Testing
* Clean Architecture
* Separation of Concerns

---

# Future Improvements

Potential future enhancements include:

* Amazon S3 document storage
* Kubernetes deployment
* Retrieval-Augmented Generation (RAG)
* Vector database integration
* Multi-model AI support
* OCR provider abstraction


# License

This project is intended for educational and portfolio purposes.
