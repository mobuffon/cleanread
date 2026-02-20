# CleanRead Setup Guide

## Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for manual setup)
- **Node.js 18+** (for manual setup)

## Option 1: Docker Setup (Recommended)

```bash
# Start all services
docker-compose up

# Or run in background
docker-compose up -d
```

**Services:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Stop services:**
```bash
docker-compose down
```

---

## Option 2: Manual Setup

### Step 1: Start Database & Redis (via Docker)

```bash
docker-compose -f docker-compose.services-only.yml up -d
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create storage directories
mkdir -p storage/uploads storage/outputs

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://cleanread:cleanread_dev@localhost:5432/cleanread
REDIS_URL=redis://localhost:6379
SECRET_KEY=$(openssl rand -hex 32)
STORAGE_PATH=./storage
DATALAB_API_KEY=your-api-key-here
EOF

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Frontend Setup (new terminal)

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Start frontend
npm run dev
```

---

## Native Backend (M1/M2/M3 Mac)

For faster PDF processing with Apple Silicon GPU acceleration:

```bash
# Start only database and Redis
docker-compose -f docker-compose.services-only.yml up -d

# Run backend natively (in backend/ directory with venv activated)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify GPU acceleration:
```python
import torch
print(torch.backends.mps.is_available())  # Should be True
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `SECRET_KEY` | JWT signing key (32+ chars) | Yes |
| `STORAGE_PATH` | File storage directory | Yes |
| `DATALAB_API_KEY` | DataLab API key | Yes |

### Frontend (`frontend/.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_URL` | Backend API URL | Yes |

---

## Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

## Troubleshooting

**Port already in use:**
```bash
docker-compose down
lsof -i :5432  # Check what's using PostgreSQL port
```

**Dependencies fail to install (macOS):**
```bash
xcode-select --install
```

**Database connection errors:**
- Ensure PostgreSQL container is running: `docker ps`
- Check DATABASE_URL matches docker-compose credentials
