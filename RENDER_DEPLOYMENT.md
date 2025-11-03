# 🚀 Render Deployment Guide for ArtScope

## ✅ Pre-Deployment Checklist

Your project is already configured for Render! Here's what's ready:

- ✅ `Procfile` - Web server + Celery worker
- ✅ `deploy.sh` - Build script with migrations
- ✅ `runtime.txt` - Python version
- ✅ `requirements.txt` - Dependencies
- ✅ Neon PostgreSQL configured
- ✅ WhiteNoise for static files
- ✅ Production security settings

---

## 🗄️ Step 1: Setup Neon PostgreSQL (Already Done!)

Your database is already configured:
```
postgresql://neondb_owner:npg_Qwn8HUECP4oz@ep-polished-glade-a1lfsvog-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

**Important:** Enable pgvector extension in Neon:
1. Go to Neon Dashboard → Your Database
2. SQL Editor → Run:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 🌐 Step 2: Deploy to Render

### Option A: Deploy via Dashboard (Recommended)

1. **Go to [Render Dashboard](https://dashboard.render.com/)**

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Or use "Public Git Repository" if not on GitHub

3. **Configure Web Service**

   **Basic Settings:**
   ```
   Name: artscope
   Region: Singapore (closest to Neon)
   Branch: main (or master)
   Root Directory: (leave empty)
   Runtime: Python 3
   ```

   **Build & Deploy:**
   ```
   Build Command: bash deploy.sh
   Start Command: gunicorn artscope.wsgi:application --bind 0.0.0.0:$PORT
   ```

4. **Add Environment Variables**

   Click "Advanced" → "Add Environment Variable":

   ```bash
   # Required
   SECRET_KEY=your-super-secret-key-here-change-this
   DATABASE_URL=postgresql://neondb_owner:npg_Qwn8HUECP4oz@ep-polished-glade-a1lfsvog-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   PYTHON_VERSION=3.12.0
   
   # Production Settings
   DEBUG=False
   ALLOWED_HOSTS=artscope.onrender.com,artscope-backend.onrender.com
   
   # Redis (Render Add-on)
   REDIS_URL=redis://red-xxxxxxxxxxxx:6379
   CELERY_BROKER_URL=redis://red-xxxxxxxxxxxx:6379
   CELERY_RESULT_BACKEND=redis://red-xxxxxxxxxxxx:6379
   
   # CORS (Add your frontend URL)
   CORS_ALLOWED_ORIGINS=https://artscope.onrender.com,https://your-frontend.com
   
   # Optional
   EMBEDDING_MODEL=clip-ViT-B-32
   MAX_UPLOAD_SIZE=10485760
   CACHE_TTL=3600
   ```

   **Generate SECRET_KEY:**
   ```python
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

5. **Click "Create Web Service"**

   Render will:
   - ✅ Clone your repository
   - ✅ Install dependencies
   - ✅ Run migrations
   - ✅ Collect static files
   - ✅ Start gunicorn server

---

## 📦 Step 3: Add Redis (For Caching & Celery)

1. **In Render Dashboard**
   - Click "New +" → "Redis"
   - Name: `artscope-redis`
   - Region: Singapore
   - Plan: Free (256MB)

2. **Connect to Web Service**
   - Copy the Internal Redis URL
   - Add to your web service environment variables:
   ```
   REDIS_URL=redis://red-xxxxxxxxxxxx:6379
   CELERY_BROKER_URL=redis://red-xxxxxxxxxxxx:6379
   CELERY_RESULT_BACKEND=redis://red-xxxxxxxxxxxx:6379
   ```

3. **Redeploy** your web service to use Redis

---

## ⚙️ Step 4: Add Celery Worker (Optional)

For background tasks (embeddings, analytics):

1. **Create Background Worker**
   - Click "New +" → "Background Worker"
   - Connect same repository
   - Name: `artscope-worker`

2. **Configure Worker**
   ```
   Build Command: bash deploy.sh
   Start Command: celery -A artscope worker --loglevel=info
   ```

3. **Copy Environment Variables**
   - Use same env vars as web service
   - Especially: DATABASE_URL, REDIS_URL, SECRET_KEY

---

## 🔧 Step 5: Configure Render Settings

### Auto-Deploy
- Enable "Auto-Deploy" for automatic updates on git push

### Health Check Path
```
Path: /api/health/
Expected Status: 200
```

### Instance Type
- Free Tier: Good for testing
- Starter ($7/mo): Recommended for production
- Standard ($25/mo): For high traffic

---

## 📝 Deployment Commands

Your `deploy.sh` runs automatically on Render:

```bash
#!/bin/bash
echo "🎨 Starting ArtScope deployment..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Initialize pgvector
python manage.py init_db

# Run migrations
python manage.py migrate --noinput

echo "✅ Deployment complete!"
```

---

## 🌍 Step 6: Access Your Application

After deployment succeeds:

### URLs:
```
Web Service: https://artscope.onrender.com
Admin Panel: https://artscope.onrender.com/admin/
API Docs: https://artscope.onrender.com/api/
Scanner: https://artscope.onrender.com/scanner/
```

### Create Superuser:

**Option 1: Via Render Shell**
```bash
# In Render Dashboard → Shell
python manage.py createsuperuser
```

**Option 2: Via Environment Variables**
Add to Render environment:
```
CREATE_SUPERUSER=true
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@artscope.com
DJANGO_SUPERUSER_PASSWORD=your-secure-password
```

---

## 🧪 Testing Your Deployment

### 1. Health Check
```bash
curl https://artscope.onrender.com/api/health/
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2025-11-03T12:00:00Z"
}
```

### 2. List Artworks
```bash
curl https://artscope.onrender.com/api/artworks/
```

### 3. Upload Artwork via Admin
1. Go to `/admin/`
2. Login with superuser
3. Add artwork with image
4. Image embedding generated automatically (if Celery + CLIP installed)

### 4. Test Scanner
1. Visit `/scanner/` on mobile (requires HTTPS)
2. Allow camera permissions
3. Point at artwork
4. Tap capture
5. See artwork details

---

## 📊 Monitoring & Logs

### View Logs in Render:
1. Dashboard → Your Service
2. Click "Logs" tab
3. Filter by: All Logs, Build Logs, Deploy Logs

### Common Log Messages:
```
✅ "Server is running" - Success
✅ "Applying migration" - Database updating
⚠️ "Connection timeout" - Redis/DB issue
❌ "ModuleNotFoundError" - Missing package
```

---

## 🐛 Troubleshooting

### Issue 1: Build Failed
**Cause:** Missing dependencies or syntax error

**Fix:**
1. Check Render build logs
2. Test locally: `pip install -r requirements.txt`
3. Ensure `requirements.txt` has all packages

### Issue 2: Static Files Not Loading
**Cause:** ALLOWED_HOSTS or WhiteNoise misconfigured

**Fix:**
Add to environment variables:
```
ALLOWED_HOSTS=your-app.onrender.com
```

### Issue 3: Database Connection Error
**Cause:** Wrong DATABASE_URL or pgvector not enabled

**Fix:**
1. Verify DATABASE_URL in Render env vars
2. Enable pgvector in Neon:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Issue 4: Camera Not Working
**Cause:** HTTPS required for camera access

**Fix:**
- Render provides HTTPS automatically
- Use `https://` not `http://`
- Allow browser camera permissions

### Issue 5: Redis Connection Failed
**Cause:** Redis not configured or wrong URL

**Fix:**
1. Create Redis instance in Render
2. Copy Internal Redis URL to REDIS_URL
3. Restart web service

---

## 🔒 Security Checklist

Before going live:

- ✅ Change SECRET_KEY to random string
- ✅ Set DEBUG=False
- ✅ Configure ALLOWED_HOSTS with your domain
- ✅ Enable HTTPS (Render does this automatically)
- ✅ Set strong admin password
- ✅ Configure CORS_ALLOWED_ORIGINS
- ✅ Review Neon PostgreSQL security settings
- ✅ Enable rate limiting (already configured)

---

## 💰 Cost Estimate

### Free Tier (Good for testing):
- Web Service: Free (spins down after inactivity)
- PostgreSQL: Neon Free (256MB, 10 connections)
- Redis: Free (256MB)
**Total: $0/month**

### Production Setup:
- Web Service: $7/mo (Starter)
- Neon PostgreSQL: $19/mo (Launch)
- Redis: $10/mo (1GB)
- Celery Worker: $7/mo (optional)
**Total: $36-43/month**

---

## 🚀 Quick Deploy Commands

### Deploy via Git:
```bash
git add .
git commit -m "Deploy to Render"
git push origin main
```
Render auto-deploys on push!

### Manual Redeploy:
1. Render Dashboard → Your Service
2. Click "Manual Deploy" → "Deploy latest commit"

---

## 📱 Mobile App Integration

Your frontend can now call:

```javascript
// Scanner endpoint
const response = await fetch('https://artscope.onrender.com/api/scan/', {
  method: 'POST',
  body: formData
});

// Get recommendations
const recs = await fetch('https://artscope.onrender.com/api/recommendations/');

// Submit feedback
await fetch('https://artscope.onrender.com/api/feedback/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ artwork: id, reaction: 'love' })
});
```

---

## ✨ Post-Deployment Tasks

1. **Upload Sample Artworks**
   - Via admin panel at `/admin/`
   - Add images for scanning

2. **Test Camera Scanning**
   - Visit `/scanner/` on phone
   - Scan uploaded artwork images

3. **Configure Analytics**
   - Check `/api/museums/{id}/analytics/`
   - Monitor visitor behavior

4. **Setup Monitoring**
   - Render provides built-in monitoring
   - Check "Metrics" tab for performance

---

## 🎯 Your Render Configuration Summary

**What's Already Configured:**

| Component | Status | Details |
|-----------|--------|---------|
| Procfile | ✅ | Gunicorn + Celery |
| deploy.sh | ✅ | Build script |
| Database | ✅ | Neon PostgreSQL |
| Static Files | ✅ | WhiteNoise |
| Security | ✅ | HTTPS, CORS |
| WSGI | ✅ | Gunicorn configured |
| Migrations | ✅ | Auto-run on deploy |

**Next Steps:**
1. Push code to GitHub
2. Connect to Render
3. Add environment variables
4. Deploy! 🚀

**Your backend will be live at:**
`https://artscope.onrender.com`
