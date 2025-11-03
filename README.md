# ArtScope - AR Museum Guide Platform

![ArtScope Logo](https://via.placeholder.com/800x200?text=ArtScope)

## 🎨 Overview

**ArtScope** is a cutting-edge, no-login AR museum guide platform that enables visitors to scan artworks and instantly receive rich multimedia information. Museums gain valuable privacy-conscious analytics while visitors enjoy a seamless, personalized experience.

## ✨ Key Features

### For Visitors (No Login Required)
- 📸 **AR Artwork Recognition** - Point your camera at any artwork for instant information
- 🎥 **360° Video Tours** - Immersive viewing experiences
- 🔊 **Audio Narration** - Listen to artwork stories and context
- 🤖 **AI-Powered Recommendations** - Discover similar artworks based on your interests
- 🌐 **Multilingual Support** - Auto-translation of artwork descriptions
- 🔒 **Privacy-First** - Anonymous sessions with no personal data collection

### For Museums
- 📊 **Advanced Analytics Dashboard** - Visitor engagement insights
- 🔥 **Heatmap Visualization** - See which artworks attract the most attention
- 📈 **Real-Time Metrics** - Monitor visitor behavior in real-time
- 💬 **Sentiment Analysis** - Understand visitor feedback with AI
- 🎯 **Artwork Performance** - Track scan counts, dwell time, and interactions
- 👥 **Role-Based Access** - Admin, curator, and staff roles
- 📤 **Bulk Upload** - Efficiently manage large artwork collections

## 🚀 Technology Stack

- **Backend**: Django 5.0 + Django REST Framework
- **Database**: PostgreSQL (Neon) with pgvector extension
- **AI/ML**: OpenAI CLIP for image embeddings
- **Caching**: Redis for performance optimization
- **Async Tasks**: Celery for background processing
- **Deployment**: Render (Python 3.12)

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │ (AR Web App)
│  (Camera)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│   REST API Gateway (DRF)        │
│  - /api/scan/                   │
│  - /api/artworks/               │
│  - /api/recommendations/        │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   Django Backend                │
│  - Vector Similarity Search     │
│  - Analytics Engine             │
│  - Recommendation System        │
└──┬────────┬────────┬────────┬───┘
   │        │        │        │
   ▼        ▼        ▼        ▼
┌────┐  ┌─────┐  ┌─────┐  ┌────┐
│ PG │  │Redis│  │Celery│  │ S3 │
│Vec │  │Cache│  │Tasks│  │Media│
└────┘  └─────┘  └─────┘  └────┘
```

## 📦 Installation

### Prerequisites
- Python 3.12+
- PostgreSQL with pgvector
- Redis
- pip

### Local Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd RealMeta
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
python manage.py init_db
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Run development server**
```bash
python manage.py runserver
```

8. **Start Celery worker** (in separate terminal)
```bash
celery -A artscope worker --loglevel=info
```

9. **Start Redis** (if not running)
```bash
redis-server
```

## 🔧 Configuration

### Database (Neon PostgreSQL)

Your Neon database is already configured in `.env`:
```
DATABASE_URL=postgresql://neondb_owner:npg_Qwn8HUECP4oz@ep-polished-glade-a1lfsvog-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

### Environment Variables

Key configurations in `.env`:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Development mode (False in production)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `OPENAI_API_KEY` - For enhanced embeddings (optional)
- `AWS_*` - S3 storage credentials (optional)

## 📡 API Endpoints

### Public Endpoints (No Authentication)

#### Scan Artwork
```http
POST /api/scan/
Content-Type: multipart/form-data

{
  "image": <file>,
  "museum_id": "uuid",
  "session_id": "uuid" (optional)
}
```

#### Get Recommendations
```http
GET /api/recommendations/?session_id=<uuid>&museum_id=<uuid>
```

#### Submit Feedback
```http
POST /api/feedback/
Content-Type: application/json

{
  "session": "uuid",
  "artwork": "uuid",
  "reaction": "love",
  "comment": "Amazing artwork!"
}
```

### Authenticated Endpoints (Museum Staff)

#### Museum Analytics
```http
GET /api/museums/{id}/analytics/?days=30
Authorization: Bearer <token>
```

#### Artwork Management
```http
GET /api/artworks/
POST /api/artworks/
PUT /api/artworks/{id}/
DELETE /api/artworks/{id}/
Authorization: Bearer <token>
```

## 🎯 Core Features Implementation

### 1. AR Artwork Recognition
```python
# Uses CLIP model for visual similarity
- Upload artwork → Generate 512-dim embedding
- Scan image → Match against database
- Return artwork with similarity score > 0.75
```

### 2. Anonymous Analytics
```python
# Privacy-first approach
- UUID-based session tracking
- No PII collection
- Opt-out capability
- Configurable data retention
```

### 3. AI Recommendations
```python
# Personalized suggestions
- Vector similarity between artworks
- Visitor interaction history
- Style and artist clustering
- Real-time score calculation
```

### 4. Sentiment Analysis
```python
# NLP-powered feedback analysis
- TextBlob sentiment scoring
- Emoji reaction tracking
- Anonymous comment analysis
```

## 🚀 Deployment (Render)

### One-Click Deploy

1. **Connect Repository** to Render
2. **Set Environment Variables**:
   - `DATABASE_URL` (from Neon)
   - `REDIS_URL`
   - `SECRET_KEY`
   - Other configs from `.env.example`

3. **Build Command**:
```bash
chmod +x deploy.sh && ./deploy.sh
```

4. **Start Command**:
```bash
gunicorn artscope.wsgi:application
```

### Celery Worker (Separate Service)
```bash
celery -A artscope worker --loglevel=info
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core
python manage.py test api

# Check coverage
coverage run --source='.' manage.py test
coverage report
```

## 📊 Database Schema

### Key Models

- **Museum** - Museum information and settings
- **Artist** - Artist profiles with style embeddings
- **Artwork** - Artworks with vector embeddings
- **VisitorSession** - Anonymous visitor tracking
- **ArtworkInteraction** - Interaction logging
- **VisitorFeedback** - Sentiment and reactions

### Vector Indexes

```sql
-- Artwork embedding index (IVFFlat)
CREATE INDEX artwork_embedding_idx 
ON core_artwork 
USING ivfflat (embedding vector_cosine_ops);
```

## 🔐 Security

- JWT authentication for museum staff
- Rate limiting (100 req/hour for anonymous)
- CORS configuration
- SQL injection protection
- XSS protection
- CSRF protection
- Secure cookie handling

## 📈 Performance Optimization

- **Redis Caching** - Frequently accessed embeddings
- **Connection Pooling** - Database optimization
- **Async Tasks** - Celery for heavy operations
- **Vector Indexes** - Fast similarity search
- **CDN Integration** - Static/media file delivery

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 👥 Team

Built with ❤️ by the ArtScope team

## 🌟 Future Enhancements

- [ ] Real-time WebSocket notifications
- [ ] Blockchain artwork provenance
- [ ] Multi-museum network mode
- [ ] AR pathfinding and navigation
- [ ] Voice-activated search
- [ ] Social sharing features
- [ ] Virtual reality integration
- [ ] Advanced NLP story generation

## 📞 Support

For issues and questions:
- 📧 Email: support@artscope.com
- 💬 Discord: [Join our community]
- 🐛 Issues: [GitHub Issues]

---

**ArtScope** - Discover Stories Beyond the Frame 🎨
