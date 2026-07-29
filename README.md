# 📄 Document Intelligence Platform

An AI-powered document processing platform built with **Django**, **Django REST Framework**, **Celery**, **Redis**, and **OpenAI**. The platform allows authenticated users to upload documents, automatically extracts text, leverages Large Language Models (LLMs) to classify and summarize content, and provides asynchronous processing with complete execution history.

The project is designed using production-oriented software engineering principles including layered architecture, asynchronous processing, repository and service patterns, transactional consistency, and robust error handling.

---

# Features

### Authentication

* JWT-based authentication
* User registration and login
* Secure access to all document endpoints
* User-specific document ownership

---

### Document Upload

* Upload PDF, image, or text documents
* Stores original document metadata
* Tracks file size, MIME type, upload timestamp, and owner

---

### AI Document Processing

After upload, documents are processed asynchronously.

Processing pipeline:

```
Upload
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
* Raw AI response

---

### Asynchronous Processing

Document processing is performed using **Celery** workers.

Benefits include:

* Non-blocking uploads
* Improved API responsiveness
* Better scalability
* Retry support
* Separation of API and background processing

---

### Processing History

Every processing attempt is recorded.

Each execution stores:

* Status
* Start time
* Completion time
* Processing duration
* Error message (if any)

This provides complete auditability of document processing.

---

### Retry Failed Processing

Failed processing jobs can be retried without uploading the document again.

The retry flow:

```
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

* database transactions
* row-level locking (`select_for_update`)
* `transaction.on_commit()`

to prevent duplicate processing and race conditions.

---

### Search and Filtering

Documents can be filtered by:

* processing status
* document type
* confidence score
* filename
* summary text

Pagination is supported for efficient retrieval.

---

# Architecture

The project follows a layered architecture.

```
               Client

                  │
                  ▼

        Django REST ViewSets

                  │
                  ▼

        Service Layer (Business Logic)

                  │
                  ▼

        Repository Layer (Database)

                  │
                  ▼

             PostgreSQL / SQLite

                  ▲
                  │

          Celery Background Worker

                  │
                  ▼

       OCR / Text Extraction Service

                  │
                  ▼

             OpenAI API
```

---

# Project Structure

```
DocumentIntelligencePlatform/

├── apps/
│   └── documents/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       └── tasks.py
│
├── repositories/
│   └── document_repository.py
│
├── services/
│   ├── document_service.py
│   ├── extraction_service.py
│   ├── ai_document_service.py
│   └── exceptions.py
│
├── config/
│
├── media/
│
└── manage.py
```

---

# Technology Stack

## Backend

* Python
* Django
* Django REST Framework

## Database

* SQLite (development)
* PostgreSQL (planned for production)

## Authentication

* JWT Authentication

## Background Processing

* Celery
* Redis

## AI

* OpenAI API

## OCR / Text Extraction

* PDF and image text extraction services

---

# API Endpoints

## Authentication

```
POST /api/auth/register/
POST /api/auth/login/
```

---

## Documents

```
POST   /api/documents/
GET    /api/documents/
GET    /api/documents/{id}/
POST   /api/documents/{id}/retry/
```

---

# Processing Lifecycle

```
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

# Design Decisions

## Repository Pattern

All database operations are isolated from business logic.

Advantages:

* cleaner services
* easier unit testing
* centralized data access
* separation of concerns

---

## Service Layer

Business logic is separated from API controllers.

Responsibilities include:

* validation
* orchestration
* transaction management
* AI integration
* retry logic

---

## Asynchronous Processing

Long-running AI tasks execute in background workers.

Advantages:

* improved response time
* scalability
* fault isolation
* retry capability

---

## Transactional Retry

Retry operations use:

* `transaction.atomic()`
* `select_for_update()`
* `transaction.on_commit()`

to ensure only one retry request can queue processing for a document at a time.

---

# Error Handling

Processing failures are recorded without crashing the application.

Each failed execution stores:

* status
* error message
* execution duration

Users can retry failed jobs without re-uploading files.

---

# Security

* JWT authentication
* User-specific document ownership
* Protected API endpoints
* Database transaction safety
* Row-level locking during retries

---

# Future Improvements

* Docker Compose support
* PostgreSQL migration
* OpenAPI / Swagger documentation
* Automated testing
* CI/CD pipeline
* Kubernetes deployment
* S3 document storage
* Multi-provider LLM support
* Prompt versioning
* Token usage tracking
* Cost analytics
* WebSocket processing notifications
* Document versioning

---

# Key Engineering Concepts Demonstrated

* RESTful API Design
* Repository Pattern
* Service Layer Pattern
* Dependency Injection
* Background Job Processing
* Event-Driven Architecture
* Transaction Management
* Row-Level Locking
* Asynchronous Processing
* AI Integration
* Retry Mechanisms
* Error Recovery
* Search and Filtering
* Pagination
* JWT Authentication
* Clean Architecture
* Separation of Concerns

---

# License

This project is intended for educational and portfolio purposes.
