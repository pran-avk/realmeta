# Render Deployment Configuration

## Quick Setup Guide

### 1. **Before Deploying - Enable pgvector in Neon**
⚠️ **CRITICAL**: Do this FIRST or deployment will fail!

1. Go to https://console.neon.tech/
2. Select your database
3. Click **SQL Editor**
4. Run this command:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

### 2. **Create Web Service on Render**

**Repository**: `https://github.com/pran-avk/realmeta`

**Configuration:**

| Field | Value |
|-------|-------|
| **Name** | `artscope` (or your choice) |
| **Region** | Choose closest to your Neon database |
| **Branch** | `main` |
| **Root Directory** | `./` |
| **Runtime** | `Python 3` |
| **Build Command** | `bash deploy.sh` |
| **Start Command** | `gunicorn artscope.wsgi:application` |

---

### 3. **Environment Variables**

Add these in Render Dashboard → Environment:

```bash
# Django Core
SECRET_KEY=c*nvuc(oy*29017knmo7@_(n9a-3ny6!po=_v%b-*g7ic_p3^@
DEBUG=False
DJANGO_SETTINGS_MODULE=artscope.settings

# Database (Your Neon PostgreSQL)
DATABASE_URL=postgresql://neondb_owner:npg_eX2Cu1dbNzfF@ep-curly-boat-ahq7twdx-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Allowed Hosts (UPDATE with your Render URL)
ALLOWED_HOSTS=artscope.onrender.com,*.onrender.com,localhost,127.0.0.1

# Optional: Redis (if you set up Redis on Render)
# REDIS_URL=redis://your-redis-url:6379/0
# CELERY_BROKER_URL=redis://your-redis-url:6379/0
# CELERY_RESULT_BACKEND=redis://your-redis-url:6379/0

# Optional: Superuser creation during deployment
# CREATE_SUPERUSER=true
# DJANGO_SUPERUSER_USERNAME=admin
# DJANGO_SUPERUSER_EMAIL=admin@example.com
# DJANGO_SUPERUSER_PASSWORD=your-secure-password
```

---

### 4. **Deploy!**

Click **"Create Web Service"** and watch the build logs.

**Build Process:**
1. ✅ Install Python dependencies
2. ✅ Collect static files
3. ✅ Initialize pgvector extension
4. ✅ Run database migrations
5. ✅ Start Gunicorn server

**Expected build time:** 3-5 minutes

---

### 5. **Post-Deployment**

Once deployed, your app will be at:
```
https://artscope.onrender.com
```

**Update ALLOWED_HOSTS:**
1. Copy your Render URL
2. Update the `ALLOWED_HOSTS` environment variable
3. Trigger a manual deploy (or just restart)

**Create Superuser (if not auto-created):**
1. Go to Render Dashboard → Shell
2. Run:
```bash
python manage.py createsuperuser
```

---

### 6. **Access Your App**

- 🏠 **Homepage**: https://artscope.onrender.com/
- 📷 **Scanner**: https://artscope.onrender.com/scanner/
- 🎨 **Artwork Details**: https://artscope.onrender.com/artwork-details/
- 🔧 **Admin Panel**: https://artscope.onrender.com/admin/
- 🚀 **API**: https://artscope.onrender.com/api/

---

## Troubleshooting

### Build Fails with "vector type does not exist"
- You forgot to enable pgvector in Neon
- Go to Neon SQL Editor and run: `CREATE EXTENSION IF NOT EXISTS vector;`

### "Bad Request (400)"
- ALLOWED_HOSTS doesn't include your Render URL
- Update ALLOWED_HOSTS environment variable

### Static Files Not Loading
- Render runs collectstatic automatically (in deploy.sh)
- Check build logs to confirm it ran

### Database Connection Issues
- Verify DATABASE_URL is correct in environment variables
- Check Neon database is active and connection string is valid

---

## What's Deployed

✅ Django 5.0 with REST API  
✅ PostgreSQL with pgvector (512-dimensional embeddings)  
✅ WhiteNoise for static files  
✅ Gunicorn production server  
✅ HTTPS automatic (Render provides SSL)  
✅ Native WebRTC camera scanning  
✅ 14+ API endpoints  
✅ Admin panel  
✅ 3 frontend templates  

**Note:** AI features (CLIP, torch) are optional and NOT installed by default to keep deployment lightweight. Enable them later if needed.

---

## Need Help?

- **Render Docs**: https://render.com/docs/deploy-django
- **Django Docs**: https://docs.djangoproject.com/
- **Neon Docs**: https://neon.tech/docs/

Good luck! 🚀
