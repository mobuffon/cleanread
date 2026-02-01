# CleanRead Quick Start Guide

Get CleanRead up and running in 5 minutes! 🚀

## Prerequisites

Choose one:
- **Option A**: Docker & Docker Compose (recommended)
- **Option B**: Python 3.9+, Node.js 18+, PostgreSQL, Redis

## Option A: Docker Quick Start (Recommended)

```bash
# 1. Clone the repository
git clone <your-repo>
cd clean_read

# 2. Start everything with Docker
docker-compose up

# 3. Open your browser
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000/docs
```

That's it! 🎉

### Try It Out

1. Drag and drop a PDF file
2. Click "Convert to EPUB"
3. Download your EPUB file
4. Transfer to Kindle and enjoy!

## Option B: Manual Quick Start

### 1. Backend Setup (Terminal 1)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "DATABASE_URL=postgresql://cleanread:cleanread_dev@localhost:5432/cleanread" > .env
echo "REDIS_URL=redis://localhost:6379" >> .env
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "STORAGE_PATH=./storage" >> .env

# Create storage directories
mkdir -p storage/uploads storage/outputs

# Start backend
uvicorn app.main:app --reload
```

### 2. Frontend Setup (Terminal 2)

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Start frontend
npm run dev
```

### 3. Open Browser

- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

## Testing the Application

### 1. Upload a Test PDF

You can use any PDF file. For testing, you can:
- Download a sample paper from arXiv.org
- Use any PDF book or document
- Create a simple test PDF

### 2. Convert to EPUB

1. Go to http://localhost:5173
2. Drag and drop your PDF
3. Click "Convert to EPUB"
4. Wait for processing (should be quick for small files)
5. Download the EPUB file

### 3. Test on Kindle

1. Connect your Kindle via USB or use Send to Kindle
2. Copy the EPUB file to your Kindle
3. Open and read with improved formatting!

## Troubleshooting

### Backend won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# If something is using it, kill it
kill -9 <PID>
```

### Frontend won't start

```bash
# Check if port 5173 is in use
lsof -i :5173

# Clear npm cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Docker issues

```bash
# Stop all containers
docker-compose down

# Remove volumes and start fresh
docker-compose down -v
docker-compose up --build
```

### Database connection error

```bash
# Make sure PostgreSQL is running
# macOS:
brew services start postgresql

# Ubuntu:
sudo systemctl start postgresql

# Create database
psql postgres
CREATE DATABASE cleanread;
CREATE USER cleanread WITH PASSWORD 'cleanread_dev';
GRANT ALL PRIVILEGES ON DATABASE cleanread TO cleanread;
\q
```

### Redis connection error

```bash
# Make sure Redis is running
# macOS:
brew services start redis

# Ubuntu:
sudo systemctl start redis

# Test connection
redis-cli ping
# Should return: PONG
```

## Common Commands

### Docker Commands

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild containers
docker-compose up --build
```

### Development Commands

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev

# Run tests
cd backend && pytest
cd frontend && npm test
```

## What's Next?

### Phase 1 - Current Features ✅
- ✅ PDF upload
- ✅ Basic conversion
- ✅ EPUB download
- ✅ Modern UI

### Phase 2 - Coming Soon
- 🔜 User authentication
- 🔜 Conversion history
- 🔜 Send to Kindle email
- 🔜 Advanced conversion options

### Phase 3 - Future
- 🔮 URL scraper
- 🔮 Chrome extension
- 🔮 Email integration
- 🔮 Batch processing

## Need More Help?

- 📖 [Setup Guide](SETUP.md) - Detailed setup instructions
- 🏗️ [Architecture](ARCHITECTURE.md) - System architecture
- 🤝 [Contributing](CONTRIBUTING.md) - Contribution guidelines
- 🐛 [GitHub Issues](https://github.com/yourusername/cleanread/issues)

## Support

If you run into issues:

1. Check the logs:
   ```bash
   # Docker
   docker-compose logs backend
   docker-compose logs frontend
   
   # Manual
   # Logs appear in terminal where services are running
   ```

2. Check the [Troubleshooting section](SETUP.md#troubleshooting)

3. Open an issue on GitHub

## Success Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173
- [ ] Can access API docs at http://localhost:8000/docs
- [ ] Can upload a PDF file
- [ ] Can convert PDF to EPUB
- [ ] Can download EPUB file

If all checked, you're ready to go! Happy reading! 📚✨
