# CleanRead Architecture

This document provides a detailed overview of the CleanRead system architecture.

## System Overview

CleanRead is a web application that converts PDF documents into EPUB files optimized for e-readers. The system follows a modern microservices-inspired architecture with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (Client)                         │
│                 React + TypeScript + Vite                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS/REST API
┌────────────────────────▼────────────────────────────────────┐
│                   API Gateway (FastAPI)                     │
│                      CORS, Auth, Routing                    │
└────┬──────────────┬─────────────────┬──────────────────────┘
     │              │                 │
     ▼              ▼                 ▼
┌─────────┐  ┌──────────────┐  ┌──────────┐
│  Upload │  │  Conversion  │  │  User    │
│ Service │  │   Service    │  │ Service  │
└────┬────┘  └──────┬───────┘  └──────────┘
     │              │
     ▼              ▼
┌─────────────────────────────────────────┐
│         Celery Task Queue (Redis)        │
│    - PDF Processing                      │
│    - EPUB Generation                     │
│    - Email Delivery                      │
└─────────────────────────────────────────┘
```

## Technology Stack

### Frontend Layer

**Framework: React 18 + TypeScript**
- **State Management**: React Query (TanStack Query)
- **Styling**: TailwindCSS
- **Build Tool**: Vite
- **HTTP Client**: Axios
- **Icons**: Lucide React

**Key Responsibilities:**
- User interface and experience
- File upload handling (drag & drop)
- Real-time conversion status updates
- Download management

### Backend Layer

**Framework: FastAPI (Python)**
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Authentication**: JWT (python-jose)
- **Task Queue**: Celery + Redis

**Key Responsibilities:**
- API endpoints and routing
- Business logic orchestration
- Authentication and authorization
- File storage management
- Job queue management

### Data Layer

**Primary Database: PostgreSQL 15**
- User accounts
- Conversion jobs and history
- File metadata
- System configuration

**Cache & Queue: Redis 7**
- Celery broker and result backend
- Session storage
- Rate limiting
- Temporary data caching

**File Storage:**
- Local filesystem (development)
- S3-compatible storage (production)

### Processing Layer

**PDF Conversion: marker-pdf**
- AI-powered layout detection
- Multi-column handling
- Header/footer removal
- Image extraction

**EPUB Generation: Custom Implementation**
- EPUB 3.0 specification
- Reflowable layout
- Metadata embedding
- Image optimization

## Data Flow

### 1. PDF Upload Flow

```
User selects PDF
    ↓
Frontend validates file (type, size)
    ↓
POST /api/v1/upload
    ↓
Backend saves to storage
    ↓
Returns file_id
    ↓
Frontend stores file_id
```

### 2. Conversion Flow

```
User clicks "Convert"
    ↓
POST /api/v1/convert {file_id}
    ↓
Create conversion job
    ↓
Enqueue Celery task
    ↓
Return job_id
    ↓
Celery worker processes PDF
    ↓
Generate EPUB
    ↓
Save to storage
    ↓
Update job status
```

### 3. Download Flow

```
Frontend polls GET /api/v1/convert/status/{job_id}
    ↓
Status = "completed"
    ↓
GET /api/v1/convert/download/{job_id}
    ↓
Return EPUB file
    ↓
Browser downloads file
```

## API Design

### RESTful Endpoints

```
GET  /                          - Root/health check
GET  /api/v1/health            - Health check
POST /api/v1/upload            - Upload PDF
POST /api/v1/convert           - Start conversion
GET  /api/v1/convert/status/:id - Check status
GET  /api/v1/convert/download/:id - Download EPUB
```

### Request/Response Format

All API responses follow this structure:

```json
{
  "status": "success|error",
  "data": {},
  "message": "Human readable message"
}
```

### Error Handling

Errors use standard HTTP status codes:
- `400`: Bad Request (invalid input)
- `401`: Unauthorized
- `404`: Not Found
- `413`: Payload Too Large
- `500`: Internal Server Error

## Security

### Authentication (Phase 2)

- JWT tokens for stateless authentication
- Refresh token rotation
- Token expiration: 7 days
- Password hashing: bcrypt

### File Security

- File type validation (PDF only)
- File size limits (50MB default)
- Virus scanning (future)
- Automatic cleanup after 24 hours

### API Security

- CORS configuration
- Rate limiting
- Input validation (Pydantic)
- SQL injection prevention (ORM)
- XSS prevention

## Scalability Considerations

### Horizontal Scaling

**Frontend:**
- Static files served via CDN
- Stateless design
- Can scale infinitely

**Backend:**
- Stateless API design
- Can run multiple instances
- Load balancer distribution

**Workers:**
- Celery workers can scale horizontally
- Add workers based on queue length
- GPU workers for heavy processing

### Vertical Scaling

**Database:**
- Connection pooling
- Read replicas for queries
- Partitioning by date

**Storage:**
- S3 for unlimited storage
- CloudFront for fast delivery

### Caching Strategy

- Redis for session data
- Browser caching for static assets
- API response caching where appropriate

## Monitoring & Observability

### Logging

- Structured logging (JSON)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request/response logging
- Error tracking

### Metrics (Future)

- Request rate and latency
- Conversion success/failure rate
- Queue length and processing time
- Storage usage

### Health Checks

- `/health` endpoint
- Database connectivity check
- Redis connectivity check
- Disk space monitoring

## Development Workflow

### Local Development

1. Clone repository
2. Start Docker Compose
3. Access frontend at `localhost:5173`
4. Access API at `localhost:8000`

### Testing Strategy

**Backend:**
- Unit tests: pytest
- Integration tests: pytest + test database
- API tests: pytest + TestClient

**Frontend:**
- Component tests: Vitest
- Integration tests: React Testing Library
- E2E tests: Playwright (future)

### CI/CD Pipeline (Future)

```
Push to GitHub
    ↓
Run linters
    ↓
Run tests
    ↓
Build Docker images
    ↓
Deploy to staging
    ↓
Run smoke tests
    ↓
Deploy to production
```

## Deployment Architecture

### Development

```
Docker Compose
├── Frontend (Vite dev server)
├── Backend (uvicorn --reload)
├── PostgreSQL
├── Redis
└── Celery Worker
```

### Production

```
Kubernetes Cluster
├── Frontend Pods (Nginx + static files)
├── Backend Pods (uvicorn)
├── Celery Worker Pods
├── PostgreSQL (managed service)
├── Redis (managed service)
└── Load Balancer
```

## Performance Optimization

### Frontend

- Code splitting
- Lazy loading
- Image optimization
- Bundle size optimization

### Backend

- Async I/O (FastAPI)
- Connection pooling
- Batch processing
- Caching

### Conversion

- GPU acceleration
- Batch processing
- Optimized parameters
- Parallel processing

## Future Enhancements

1. **Real-time Updates**: WebSocket for live progress
2. **Batch Conversion**: Multiple files at once
3. **URL Scraping**: Convert web articles
4. **Email Integration**: Forward newsletters
5. **Chrome Extension**: Right-click to convert
6. **OCR Support**: Scan-based PDFs
7. **Formula Support**: LaTeX rendering
8. **Multi-language**: i18n support

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [EPUB 3 Specification](https://www.w3.org/publishing/epub3/)
- [marker-pdf GitHub](https://github.com/VikParuchuri/marker)
