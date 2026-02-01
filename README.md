# CleanRead 📚

Convert PDFs, academic papers, and web content into high-quality EPUB files optimized for Kindle and e-ink devices.

## 🎯 Problem Statement

Reading PDFs on Kindle is painful due to:
- Fixed layouts that don't reflow
- Multi-column formats
- Poor font rendering
- Unreadable on small e-ink screens

**CleanRead** solves this by intelligently extracting and reformatting content into proper EPUB files.

## ✨ Features

### Current (Phase 1 - MVP)
- 📤 Drag-and-drop PDF upload
- 🔄 Intelligent PDF to EPUB conversion
- 📥 Direct EPUB download
- 🎨 Clean, responsive UI

### Planned (Phase 2+)
- 🔐 User authentication & history
- 📧 Send to Kindle via email
- 🌐 URL scraper for web articles
- 🔌 Chrome extension
- 📮 Email forwarding for newsletters
- 📚 Batch processing & collections
- 🧮 LaTeX formula support

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Celery** + **Redis** - Async task processing
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **pdf2epub** - PDF conversion engine

### Frontend
- **React** + **TypeScript**
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **React Query** - API state management

### Infrastructure
- **Docker** - Containerization
- **MinIO/S3** - File storage

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (optional)

### Development Setup

1. **Clone the repository**
```bash
git clone <repo-url>
cd clean_read
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

4. **Using Docker (Recommended)**
```bash
docker-compose up
```

## 📁 Project Structure

```
clean_read/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Config, security, dependencies
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   ├── tasks/         # Celery tasks
│   │   └── main.py        # FastAPI app entry
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API clients
│   │   ├── hooks/         # Custom React hooks
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

Create `.env` files in backend and frontend directories:

**backend/.env**
```
DATABASE_URL=postgresql://user:password@localhost/cleanread
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
STORAGE_PATH=./storage
```

**frontend/.env**
```
VITE_API_URL=http://localhost:8000
```

## 📖 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📝 Development Roadmap

- [x] Project structure
- [ ] Basic PDF upload & conversion
- [ ] Frontend UI
- [ ] User authentication
- [ ] Async job processing
- [ ] Send to Kindle
- [ ] URL scraper
- [ ] Chrome extension
- [ ] Email integration

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines first.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [pdf2epub](https://github.com/overcuriousity/pdf2epub) - PDF conversion engine
- [marker-pdf](https://github.com/VikParuchuri/marker) - PDF processing
