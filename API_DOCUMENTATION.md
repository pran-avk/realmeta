# 🔌 ArtScope API Documentation

## Base URL
```
Development: http://localhost:8000/api
Production: https://your-app.onrender.com/api
```

## Authentication

### Obtain JWT Token
```http
POST /api/token/
Content-Type: application/json

{
  "username": "museum_admin",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh Token
```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Using Token
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## 🎨 Public Endpoints (No Authentication Required)

### 1. Scan Artwork (Core AR Feature)

**Endpoint:** `POST /api/scan/`

**Description:** Upload an image of artwork to identify it and get detailed information.

**Request:**
```http
POST /api/scan/
Content-Type: multipart/form-data

image: <binary file>
museum_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
session_id: "optional-existing-session-uuid"
```

**PowerShell Example:**
```powershell
$museum_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
$image_path = "C:\Users\kp755\Pictures\starry_night.jpg"

curl -X POST http://localhost:8000/api/scan/ `
  -F "image=@$image_path" `
  -F "museum_id=$museum_id"
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/api/scan/"
files = {"image": open("starry_night.jpg", "rb")}
data = {"museum_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Response (200 OK):**
```json
{
  "artwork": {
    "id": "artwork-uuid",
    "title": "Starry Night",
    "description": "A swirling night sky over a French village...",
    "year_created": 1889,
    "category": "painting",
    "artist": {
      "id": "artist-uuid",
      "name": "Vincent van Gogh",
      "birth_year": 1853,
      "death_year": 1890,
      "style": "Post-Impressionism"
    },
    "museum": {
      "id": "museum-uuid",
      "name": "Museum of Modern Art",
      "location": "New York, NY"
    },
    "image": "https://storage.example.com/artworks/starry_night.jpg",
    "video_360": "https://storage.example.com/videos/starry_night_360.mp4",
    "audio_narration": "https://storage.example.com/audio/starry_night.mp3",
    "tags": ["night", "stars", "landscape", "post-impressionism"],
    "historical_context": "Painted during van Gogh's stay at the asylum...",
    "scan_count": 1523,
    "avg_dwell_time_seconds": 120.5
  },
  "similarity_score": 0.94,
  "session_id": "new-session-uuid",
  "recommendations": [
    {
      "id": "artwork-uuid-2",
      "title": "The Bedroom",
      "artist_name": "Vincent van Gogh",
      "category": "painting",
      "image": "https://storage.example.com/artworks/bedroom.jpg"
    },
    {
      "id": "artwork-uuid-3",
      "title": "Sunflowers",
      "artist_name": "Vincent van Gogh",
      "category": "painting",
      "image": "https://storage.example.com/artworks/sunflowers.jpg"
    }
  ]
}
```

**Error Responses:**
```json
// 404 - No match found
{
  "error": "No confident match found",
  "best_score": 0.42
}

// 400 - Invalid request
{
  "image": ["This field is required"],
  "museum_id": ["This field is required"]
}
```

---

### 2. Get Recommendations

**Endpoint:** `GET /api/recommendations/`

**Description:** Get personalized artwork recommendations based on viewing history.

**Request:**
```http
GET /api/recommendations/?session_id={session-uuid}&museum_id={museum-uuid}
```

**Example:**
```powershell
curl http://localhost:8000/api/recommendations/?session_id=abc123&museum_id=def456
```

**Response (200 OK):**
```json
[
  {
    "artwork": {
      "id": "artwork-uuid",
      "title": "Water Lilies",
      "artist_name": "Claude Monet",
      "category": "painting",
      "image": "https://storage.example.com/artworks/water_lilies.jpg"
    },
    "score": 0.87,
    "reason": "Based on your viewing history"
  },
  {
    "artwork": {
      "id": "artwork-uuid-2",
      "title": "Impression, Sunrise",
      "artist_name": "Claude Monet",
      "category": "painting",
      "image": "https://storage.example.com/artworks/impression.jpg"
    },
    "score": 0.82,
    "reason": "Based on your viewing history"
  }
]
```

---

### 3. Submit Feedback

**Endpoint:** `POST /api/feedback/`

**Description:** Submit visitor feedback for an artwork.

**Request:**
```http
POST /api/feedback/
Content-Type: application/json

{
  "session": "session-uuid",
  "artwork": "artwork-uuid",
  "reaction": "love",
  "comment": "Absolutely stunning! The colors are so vibrant."
}
```

**Reaction Options:** `"love"`, `"like"`, `"neutral"`, `"dislike"`

**Example:**
```powershell
curl -X POST http://localhost:8000/api/feedback/ `
  -H "Content-Type: application/json" `
  -d '{
    "session": "abc-123",
    "artwork": "def-456",
    "reaction": "love",
    "comment": "Amazing artwork!"
  }'
```

**Response (201 Created):**
```json
{
  "id": "feedback-uuid",
  "session": "session-uuid",
  "artwork": "artwork-uuid",
  "reaction": "love",
  "comment": "Absolutely stunning! The colors are so vibrant.",
  "sentiment_score": 0.85,
  "created_at": "2025-11-03T14:30:00Z"
}
```

---

### 4. Log Interaction

**Endpoint:** `POST /api/interactions/`

**Description:** Log visitor interactions with artworks.

**Request:**
```http
POST /api/interactions/
Content-Type: application/json

{
  "session": "session-uuid",
  "artwork": "artwork-uuid",
  "interaction_type": "play_audio",
  "dwell_time_seconds": 120
}
```

**Interaction Types:**
- `"scan"` - Artwork scan
- `"view_details"` - View details
- `"play_audio"` - Play audio narration
- `"watch_video"` - Watch 360° video
- `"view_related"` - View related artworks

**Response (201 Created):**
```json
{
  "id": "interaction-uuid",
  "session": "session-uuid",
  "artwork": "artwork-uuid",
  "artwork_title": "Starry Night",
  "interaction_type": "play_audio",
  "timestamp": "2025-11-03T14:30:00Z",
  "dwell_time_seconds": 120
}
```

---

### 5. Opt Out of Analytics

**Endpoint:** `POST /api/opt-out/`

**Description:** Allow visitors to opt out of analytics tracking.

**Request:**
```http
POST /api/opt-out/
Content-Type: application/json

{
  "session_id": "session-uuid"
}
```

**Response (200 OK):**
```json
{
  "message": "Successfully opted out of analytics"
}
```

---

### 6. List Museums

**Endpoint:** `GET /api/museums/`

**Description:** Get list of all active museums.

**Request:**
```http
GET /api/museums/
```

**Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/museums/?page=2",
  "previous": null,
  "results": [
    {
      "id": "museum-uuid",
      "name": "The Metropolitan Museum of Art",
      "description": "One of the world's largest art museums",
      "location": "New York, NY",
      "contact_email": "info@metmuseum.org",
      "website": "https://www.metmuseum.org",
      "logo": "https://storage.example.com/logos/met.jpg",
      "artwork_count": 2543,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

### 7. List Artworks

**Endpoint:** `GET /api/artworks/`

**Description:** Browse artworks with filtering and search.

**Query Parameters:**
- `museum` - Filter by museum UUID
- `artist` - Filter by artist UUID
- `category` - Filter by category (`painting`, `sculpture`, etc.)
- `search` - Search in title/description/tags
- `page` - Page number (default: 1)
- `page_size` - Results per page (default: 20)

**Request:**
```http
GET /api/artworks/?museum=museum-uuid&category=painting&search=van+gogh
```

**Response (200 OK):**
```json
{
  "count": 42,
  "next": "http://localhost:8000/api/artworks/?page=2",
  "previous": null,
  "results": [
    {
      "id": "artwork-uuid",
      "title": "Starry Night",
      "artist_name": "Vincent van Gogh",
      "museum_name": "MoMA",
      "category": "painting",
      "year_created": 1889,
      "image": "https://storage.example.com/artworks/starry_night.jpg",
      "scan_count": 1523,
      "is_on_display": true
    }
  ]
}
```

---

### 8. Get Artwork Details

**Endpoint:** `GET /api/artworks/{id}/`

**Description:** Get complete artwork information.

**Request:**
```http
GET /api/artworks/artwork-uuid/
```

**Response (200 OK):**
```json
{
  "id": "artwork-uuid",
  "museum": {
    "id": "museum-uuid",
    "name": "Museum of Modern Art",
    "location": "New York, NY"
  },
  "artist": {
    "id": "artist-uuid",
    "name": "Vincent van Gogh",
    "birth_year": 1853,
    "death_year": 1890,
    "nationality": "Dutch",
    "style": "Post-Impressionism"
  },
  "title": "Starry Night",
  "description": "A swirling night sky over a French village...",
  "year_created": 1889,
  "category": "painting",
  "medium": "Oil on canvas",
  "dimensions": "73.7 cm × 92.1 cm",
  "gallery_location": "Level 5, Gallery 3",
  "room_number": "503",
  "image": "https://storage.example.com/artworks/starry_night.jpg",
  "video_360": "https://storage.example.com/videos/starry_night_360.mp4",
  "audio_narration": "https://storage.example.com/audio/starry_night.mp3",
  "tags": ["night", "stars", "landscape", "post-impressionism"],
  "historical_context": "Painted during van Gogh's stay at the asylum...",
  "provenance": "Acquired from the artist's collection...",
  "acquisition_date": "1941-06-01",
  "scan_count": 1523,
  "view_count": 8452,
  "avg_dwell_time_seconds": 120.5,
  "is_on_display": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### 9. Find Similar Artworks

**Endpoint:** `GET /api/artworks/{id}/similar/`

**Description:** Find visually similar artworks using vector embeddings.

**Request:**
```http
GET /api/artworks/artwork-uuid/similar/
```

**Response (200 OK):**
```json
[
  {
    "artwork": {
      "id": "artwork-uuid-2",
      "title": "The Bedroom",
      "artist_name": "Vincent van Gogh",
      "category": "painting",
      "image": "https://storage.example.com/artworks/bedroom.jpg"
    },
    "similarity_score": 0.89
  },
  {
    "artwork": {
      "id": "artwork-uuid-3",
      "title": "Café Terrace at Night",
      "artist_name": "Vincent van Gogh",
      "category": "painting",
      "image": "https://storage.example.com/artworks/cafe.jpg"
    },
    "similarity_score": 0.85
  }
]
```

---

### 10. Health Check

**Endpoint:** `GET /api/health/`

**Description:** Check API health status.

**Request:**
```http
GET /api/health/
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-03T14:30:00.123456Z"
}
```

---

## 🔒 Authenticated Endpoints (Museum Staff Only)

### 11. Get Museum Analytics

**Endpoint:** `GET /api/museums/{id}/analytics/`

**Description:** Get comprehensive analytics for a museum.

**Authentication:** Required (JWT Token)

**Query Parameters:**
- `days` - Number of days to analyze (default: 30)

**Request:**
```http
GET /api/museums/museum-uuid/analytics/?days=30
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response (200 OK):**
```json
{
  "museum_name": "The Metropolitan Museum of Art",
  "period_days": 30,
  "total_sessions": 15234,
  "total_interactions": 84521,
  "avg_session_duration_minutes": 45.2,
  "avg_dwell_time_seconds": 120.5,
  "top_artworks": [
    {
      "artwork__title": "Starry Night",
      "artwork__id": "artwork-uuid",
      "scan_count": 1523
    },
    {
      "artwork__title": "Mona Lisa",
      "artwork__id": "artwork-uuid-2",
      "scan_count": 1342
    }
  ],
  "interaction_breakdown": [
    {
      "interaction_type": "scan",
      "count": 15234
    },
    {
      "interaction_type": "play_audio",
      "count": 8451
    },
    {
      "interaction_type": "watch_video",
      "count": 3425
    }
  ],
  "daily_trends": [
    {
      "day": "2025-10-04",
      "visitors": 523
    },
    {
      "day": "2025-10-05",
      "visitors": 612
    }
  ]
}
```

---

### 12. Get Interaction Heatmap

**Endpoint:** `GET /api/museums/{id}/heatmap/`

**Description:** Get visitor interaction heatmap data.

**Authentication:** Required

**Query Parameters:**
- `days` - Number of days to analyze (default: 7)

**Request:**
```http
GET /api/museums/museum-uuid/heatmap/?days=7
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response (200 OK):**
```json
{
  "data": [
    [12, 15, 18, 25, 42, 56, 78, 92, 104, 98, 87, 75, 65, 58, 52, 48, 45, 42, 38, 32, 25, 18, 15, 12],
    [10, 13, 16, 22, 38, 52, 72, 88, 98, 95, 82, 70, 60, 55, 50, 45, 42, 38, 35, 30, 22, 16, 13, 10]
  ],
  "days": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
  "hours": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
}
```

---

### 13. Get Artwork Insights

**Endpoint:** `GET /api/artworks/{id}/insights/`

**Description:** Get detailed analytics for a specific artwork.

**Authentication:** Required

**Request:**
```http
GET /api/artworks/artwork-uuid/insights/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response (200 OK):**
```json
{
  "artwork_title": "Starry Night",
  "total_scans": 1523,
  "avg_dwell_time_seconds": 120.5,
  "interaction_stats": [
    {
      "interaction_type": "scan",
      "count": 1523
    },
    {
      "interaction_type": "play_audio",
      "count": 842
    },
    {
      "interaction_type": "watch_video",
      "count": 425
    }
  ],
  "feedback_stats": [
    {
      "reaction": "love",
      "count": 523
    },
    {
      "reaction": "like",
      "count": 312
    },
    {
      "reaction": "neutral",
      "count": 45
    }
  ],
  "avg_sentiment": 0.78
}
```

---

### 14. Create Artwork

**Endpoint:** `POST /api/artworks/`

**Description:** Add a new artwork to the collection.

**Authentication:** Required

**Request:**
```http
POST /api/artworks/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: multipart/form-data

museum: museum-uuid
artist: artist-uuid
title: Starry Night
description: A swirling night sky over a French village...
year_created: 1889
category: painting
medium: Oil on canvas
dimensions: 73.7 cm × 92.1 cm
image: <binary file>
tags: ["night", "stars", "landscape"]
```

**Response (201 Created):**
```json
{
  "id": "new-artwork-uuid",
  "museum": "museum-uuid",
  "artist": "artist-uuid",
  "title": "Starry Night",
  "description": "A swirling night sky over a French village...",
  "year_created": 1889,
  "category": "painting",
  "medium": "Oil on canvas",
  "dimensions": "73.7 cm × 92.1 cm",
  "image": "https://storage.example.com/artworks/starry_night.jpg",
  "is_on_display": true
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limit exceeded) |
| 500 | Internal Server Error |

---

## Rate Limiting

- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699027200
```

---

## Testing with Postman

Import the `postman_collection.json` file included in the project for ready-to-use API tests.

---

## Need Help?

- Check `README.md` for setup instructions
- Check `ARCHITECTURE.md` for system design
- Check `QUICKSTART.md` for quick reference

---

**Built with ❤️ for museums and art lovers worldwide** 🎨
