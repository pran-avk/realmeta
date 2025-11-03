# 🚀 Quick Render Deployment Checklist

## ✅ Pre-Deployment (Already Done!)

- [x] Procfile created
- [x] deploy.sh created  
- [x] runtime.txt created
- [x] requirements.txt updated (core packages only)
- [x] Neon PostgreSQL configured
- [x] Settings.py production-ready
- [x] Static files with WhiteNoise
- [x] Security settings enabled

## 📋 Deployment Steps

### 1️⃣ Enable pgvector in Neon (IMPORTANT!)

```sql
-- Go to Neon Dashboard → SQL Editor → Run:
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2️⃣ Generate SECRET_KEY

Run locally:
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output for next step!

### 3️⃣ Deploy to Render

1. Go to https://dashboard.render.com/
2. Click "New +" → "Web Service"
3. Connect your repository

**Configure:**
```
Name: artscope
Runtime: Python 3
Build Command: bash deploy.sh
Start Command: gunicorn artscope.wsgi:application --bind 0.0.0.0:$PORT
```

### 4️⃣ Add Environment Variables

```bash
# REQUIRED - Change these!
SECRET_KEY=paste-your-generated-key-here
DATABASE_URL=postgresql://neondb_owner:npg_Qwn8HUECP4oz@ep-polished-glade-a1lfsvog-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

# Production settings
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
PYTHON_VERSION=3.12.0
```

### 5️⃣ Add Redis (Optional but Recommended)

1. Create Redis: "New +" → "Redis"
2. Copy Internal Redis URL
3. Add to web service:
```bash
REDIS_URL=redis://red-xxxxxxxxxxxx:6379
CELERY_BROKER_URL=redis://red-xxxxxxxxxxxx:6379
```

### 6️⃣ Deploy!

Click "Create Web Service" - Render will:
- Install packages
- Run migrations
- Collect static files
- Start server

### 7️⃣ Create Admin User

In Render Shell:
```bash
python manage.py createsuperuser
```

## 🧪 Test Your Deployment

```bash
# Health check
curl https://your-app.onrender.com/api/health/

# View homepage
https://your-app.onrender.com/

# Admin panel
https://your-app.onrender.com/admin/

# Scanner
https://your-app.onrender.com/scanner/
```

## 📱 Update Frontend

Update your frontend API URL to:
```javascript
const API_URL = 'https://your-app.onrender.com/api';
```

## ⚠️ Important Notes

### Camera Scanning Without AI
The basic app works NOW without heavy AI packages!
- Templates work ✅
- Admin works ✅
- Database works ✅
- APIs work ✅

For AI-powered scanning, install later:
```bash
pip install torch torchvision transformers pillow
pip install git+https://github.com/openai/CLIP.git
```

### Free Tier Limitations
- Web service spins down after 15 min inactivity
- First request after sleep takes ~30 seconds
- Upgrade to Starter ($7/mo) for always-on

### Static Files
Already configured with WhiteNoise - no S3 needed!

## 🎯 What Works RIGHT NOW

✅ Frontend templates (Welcome, Scanner, Details)
✅ Admin panel for managing artworks
✅ REST API endpoints
✅ Database with vector support (pgvector)
✅ Authentication (JWT)
✅ Static files serving
✅ HTTPS (automatic on Render)

## 🔮 Add Later (Optional)

- CLIP embeddings for AI scanning
- Celery worker for background tasks
- AWS S3 for large media files
- Custom domain

---

**Your app is ready to deploy!** 🚀

Just follow steps 1-7 above and you'll be live in ~5 minutes!
