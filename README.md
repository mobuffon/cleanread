# CleanRead

Convert PDFs into high-quality EPUB files optimized for Kindle and e-ink devices.

**Live Demo**: https://cleanread-o09g.onrender.com/ (free tier - may take a moment to wake up)

## Features

- **PDF Upload** - Drag-and-drop interface with validation
- **Smart Conversion** - AI-powered layout detection via DataLab Marker API
- **EPUB Download** - Reflowable, Kindle-optimized output
- **Image & Table Support** - Extracts images, handles tables as HTML

## Quick Start

### Using Docker (Recommended)

```bash
git clone <repo-url>
cd clean_read
docker-compose up
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Manual Setup

See [SETUP.md](SETUP.md) for detailed instructions.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, PostgreSQL, Redis, Celery |
| Frontend | React, TypeScript, Vite, TailwindCSS |
| Processing | DataLab Marker API |
| Infrastructure | Docker, Docker Compose |

## Project Structure

```
clean_read/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # API endpoints
│   │   ├── core/      # Config, security
│   │   ├── models/    # Database models
│   │   ├── services/  # Business logic
│   │   └── tasks/     # Celery tasks
│   └── alembic/       # Database migrations
├── frontend/          # React frontend
│   └── src/
│       ├── components/
│       ├── services/
│       └── context/
└── docker-compose.yml
```

## Configuration

**Required environment variables:**

```bash
# backend/.env
DATABASE_URL=postgresql://cleanread:cleanread_dev@localhost:5432/cleanread
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
DATALAB_API_KEY=your-datalab-api-key  # Get from https://datalab.to
```

```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```

## Documentation

- [SETUP.md](SETUP.md) - Development setup guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [ROADMAP.md](ROADMAP.md) - Development roadmap

## License

MIT License - see [LICENSE](LICENSE) for details.
