# Render Deployment Guide

## Quick Deploy (5 minutes)

### Step 1: Go to Render Dashboard
1. Visit: https://render.com
2. **Sign up/Login** with GitHub
3. Click **"New +"** → **"Blueprint"**

### Step 2: Connect Repository
1. **Connect GitHub** → Select `cleanread` repo
2. **Blueprint file**: `render.yaml` (auto-detected)
3. **Branch**: `main`
4. Click **"Apply"**

### Step 3: Set Environment Variables
After services are created, you need to set:

**Backend Service Environment:**
```
DATALAB_API_KEY=your_actual_api_key_here
```

**How to set:**
1. Go to **cleanread-backend** service
2. **Environment** tab
3. Add `DATALAB_API_KEY` variable
4. **Deploy** again

### Step 4: Database Migration
Once backend is running:
```bash
# Get backend service shell
# Or use Render's shell feature in dashboard
alembic upgrade head
```

---

## Your App URLs (after deployment)

- **Frontend**: https://cleanread-frontend.onrender.com
- **Backend**: https://cleanread-backend.onrender.com
- **API Docs**: https://cleanread-backend.onrender.com/docs

---

## Costs

- **Backend**: $7/month (paid plan required for 24/7)
- **Frontend**: FREE (static site)
- **PostgreSQL**: FREE (shared instance)
- **Redis**: FREE (shared instance)

**Total: $7/month**

---

## What Render Auto-Handles

✅ **SSL certificates** (HTTPS)  
✅ **Environment variables** from render.yaml  
✅ **Database connections** (auto-linked)  
✅ **Auto-deploys** on git push  
✅ **Health checks** and monitoring  
✅ **Logs and metrics**  

---

## Common Issues & Solutions

### Backend takes time to start (cold starts)
- Normal on free tier
- Paid plan eliminates this

### CORS errors
- Fixed automatically with ALLOWED_ORIGINS in render.yaml

### Database connection errors
- Check DATABASE_URL is auto-set from cleanread-db
- Verify backend service is in same region as database

---

## Manual Alternative (if Blueprint fails)

1. **Create Backend Service:**
   - New Web Service
   - Connect GitHub repo
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Create Frontend Service:**
   - New Static Site
   - Connect GitHub repo  
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`

3. **Create Databases:**
   - New PostgreSQL (free)
   - New Redis (free)

4. **Link Everything:**
   - Set environment variables to connect services