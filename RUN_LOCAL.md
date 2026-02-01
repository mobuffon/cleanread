# Run Backend Locally (with M3 Acceleration)

This guide shows how to run the backend natively on your Mac to leverage M3 GPU acceleration.

## Step 1: Stop current Docker and run services only

```bash
# Stop everything
docker-compose down

# Start only database, Redis, and frontend
docker-compose -f docker-compose.services-only.yml up -d
```

## Step 2: Set up Python environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies (this will take a few minutes)
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Create storage directories

```bash
mkdir -p storage/uploads storage/outputs
```

## Step 4: Run the backend

```bash
# Make sure you're in backend/ directory with venv activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 5: Test

Open http://localhost:5173/ and upload a PDF.

The conversion should be **5-10x faster** than Docker!

## To stop

```bash
# Stop backend: Ctrl+C in terminal

# Stop services
docker-compose -f docker-compose.services-only.yml down
```

## Troubleshooting

**Port 5432 already in use:**
```bash
docker-compose down
```

**Dependencies fail to install:**
```bash
# Install Xcode Command Line Tools if not already installed
xcode-select --install
```

**PyTorch not using M3:**
Check in Python:
```python
import torch
print(torch.backends.mps.is_available())  # Should be True
print(torch.backends.mps.is_built())      # Should be True
```
