# CleanRead Setup Guide

This guide will help you get CleanRead up and running on your local machine.

## Prerequisites

- **Python 3.9+** (for backend)
- **Node.js 18+** (for frontend)
- **Docker & Docker Compose** (optional, recommended)
- **PostgreSQL** (if not using Docker)
- **Redis** (if not using Docker)

## Quick Start with Docker (Recommended)

The easiest way to run CleanRead is using Docker Compose:

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd clean_read

# 2. Create environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Start all services
docker-compose up
```

That's it! The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Manual Setup (Without Docker)

### Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env

# 5. Update .env with your database credentials
# Edit the DATABASE_URL and REDIS_URL

# 6. Create storage directories
mkdir -p storage/uploads storage/outputs

# 7. Run the server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create .env file
cp .env.example .env

# 4. Start development server
npm run dev
```

### Database Setup

```bash
# 1. Install PostgreSQL (if not already installed)
# macOS:
brew install postgresql
brew services start postgresql

# Ubuntu:
sudo apt install postgresql

# 2. Create database
psql postgres
CREATE DATABASE cleanread;
CREATE USER cleanread WITH PASSWORD 'cleanread_dev';
GRANT ALL PRIVILEGES ON DATABASE cleanread TO cleanread;
\q

# 3. Run migrations (coming in Phase 2)
# cd backend
# alembic upgrade head
```

### Redis Setup

```bash
# macOS:
brew install redis
brew services start redis

# Ubuntu:
sudo apt install redis-server
sudo systemctl start redis
```

## Development Workflow

### Running Backend Tests

```bash
cd backend
pytest
```

### Running Frontend Tests

```bash
cd frontend
npm test
```

### Code Formatting

```bash
# Backend (Python)
cd backend
black .
ruff check .

# Frontend (TypeScript)
cd frontend
npm run lint
```

## Environment Variables

### Backend (.env)

```env
# Required
DATABASE_URL=postgresql://cleanread:cleanread_dev@localhost:5432/cleanread
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here

# Optional
STORAGE_PATH=./storage
MAX_UPLOAD_SIZE=52428800
PDF_MAX_PAGES=500
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Database Connection Error

- Verify PostgreSQL is running: `pg_isready`
- Check credentials in `.env` file
- Ensure database exists: `psql -l`

### Redis Connection Error

- Verify Redis is running: `redis-cli ping`
- Should return `PONG`

### Module Not Found Errors

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### PDF Conversion Issues

The current MVP uses a placeholder EPUB generator. For full PDF conversion:

1. Ensure `marker-pdf` is installed correctly
2. Check GPU/CPU compatibility
3. For GPU support, install appropriate PyTorch version:
   - NVIDIA: `pip install torch --index-url https://download.pytorch.org/whl/cu121`
   - AMD: `pip install torch --index-url https://download.pytorch.org/whl/rocm6.2`

## Next Steps

- [ ] Test the upload functionality
- [ ] Try converting a sample PDF
- [ ] Explore the API documentation at `/docs`
- [ ] Read the main README for feature roadmap
- [ ] Consider setting up authentication (Phase 2)

## Need Help?

- Check the [GitHub Issues](your-repo/issues)
- Read the [API Documentation](http://localhost:8000/docs)
- Review the [Architecture Overview](README.md#architecture)

## Production Deployment

For production deployment:

1. Set strong `SECRET_KEY` in backend/.env
2. Use production-grade database (managed PostgreSQL)
3. Use production-grade Redis (managed Redis)
4. Set up proper CORS origins
5. Enable HTTPS
6. Set up monitoring and logging
7. Configure file storage (S3, MinIO)
8. Set up CI/CD pipeline

See `DEPLOYMENT.md` (coming soon) for detailed production setup.
