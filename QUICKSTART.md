# ArtScope Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Clone and Setup
```powershell
# Clone repository
cd C:\Users\kp755\OneDrive\Desktop\RealMeta

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Database
Your Neon PostgreSQL is already configured! The connection string is:
```
postgresql://neondb_owner:npg_Qwn8HUECP4oz@ep-polished-glade-a1lfsvog-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

Create a `.env` file:
```powershell
copy .env.example .env
# No need to edit DATABASE_URL - it's already set!
```

### Step 3: Initialize Database
```powershell
# Run migrations
python manage.py migrate

# Initialize pgvector extension
python manage.py init_db

# Create admin user
python manage.py createsuperuser

# Create sample data (optional)
python manage.py create_sample_data
```

### Step 4: Start Services

**Terminal 1 - Django Server:**
```powershell
python manage.py runserver
```

**Terminal 2 - Celery Worker (optional for development):**
```powershell
celery -A artscope worker --loglevel=info --pool=solo
```

**Terminal 3 - Redis (if not running):**
```powershell
# Download Redis for Windows or use WSL
redis-server
```

### Step 5: Test the API

Visit: http://localhost:8000/admin
- Login with your superuser credentials
- Add a museum, artist, and artwork with an image

## 📱 Test AR Scanning

### Using Postman
1. Import `postman_collection.json`
2. Set `base_url` to `http://localhost:8000`
3. Test the `/api/scan/` endpoint with an artwork image

### Using curl
```powershell
curl -X POST http://localhost:8000/api/scan/ `
  -F "image=@path/to/artwork.jpg" `
  -F "museum_id=<museum-uuid>"
```

## 🔑 Key URLs

- **Admin Panel**: http://localhost:8000/admin
- **API Root**: http://localhost:8000/api/
- **Health Check**: http://localhost:8000/api/health/
- **API Documentation**: http://localhost:8000/api/ (browsable API)

## 🎯 Core Endpoints

### Public (No Auth)
- `POST /api/scan/` - Scan artwork
- `GET /api/recommendations/` - Get recommendations
- `POST /api/feedback/` - Submit feedback
- `GET /api/artworks/` - List artworks

### Authenticated (Museum Staff)
- `GET /api/museums/{id}/analytics/` - Get analytics
- `GET /api/museums/{id}/heatmap/` - Get heatmap
- `POST /api/artworks/` - Create artwork
- `GET /api/artworks/{id}/insights/` - Get insights

## 🔧 Configuration Tips

### For Development
- Keep `DEBUG=True` in `.env`
- Use `python manage.py runserver` for auto-reload
- Install Redis Desktop Manager for cache inspection

### For Production (Render)
1. Push code to GitHub
2. Connect to Render
3. Set environment variables
4. Deploy with `./deploy.sh`

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'X'"
```powershell
pip install -r requirements.txt
```

### "No pgvector extension"
```powershell
python manage.py init_db
```

### Redis connection error
- Make sure Redis is running
- Check `REDIS_URL` in `.env`

### Embedding generation not working
- Ensure artwork has an image uploaded
- Check Celery worker is running
- Embeddings generate in background (may take 30s)

## 📊 Sample Workflow

1. **Museum Admin** logs in → creates museum
2. **Curator** adds artists and artworks
3. **System** generates embeddings automatically (via Celery)
4. **Visitor** scans artwork → gets instant info
5. **Admin** views analytics dashboard

## 🎨 Adding Your First Artwork

1. Go to http://localhost:8000/admin
2. Add a Museum
3. Add an Artist
4. Add an Artwork:
   - Upload a clear image
   - Fill in title, description
   - Save and wait for embedding generation

5. Test scanning:
   - Use Postman to scan the same image
   - Should return a match with high similarity score!

## 💡 Pro Tips

- Use high-quality artwork images (>1024px)
- Tag artworks for better recommendations
- Enable analytics for insights
- Check Celery logs for background tasks
- Use Redis cache for frequently scanned artworks

## 🚀 Next Steps

- [ ] Deploy to Render
- [ ] Connect frontend
- [ ] Add more artworks
- [ ] Test AR scanning in real museum
- [ ] Enable S3 for media storage
- [ ] Setup monitoring and logging

## 📞 Need Help?

Check the main README.md for detailed documentation!

---

Happy coding! 🎨✨
