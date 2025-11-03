# ArtScope - Scanning Methods

## 🎯 Active Scanning Technologies

Your ArtScope app uses **TWO primary methods** for artwork identification:

### 1. 📍 **Location-Based Scanning (Geofencing)**
**How it works:**
- Museum staff uploads artwork with GPS coordinates (auto-captured during upload)
- Each artwork has a geofence radius (default: 100 meters)
- When visitor scans, app checks their GPS location
- If visitor is within geofence radius → artwork unlocked
- If visitor is too far → shows distance message

**Use case:** Ensures visitors can only scan artworks when physically present at the museum

**Files:**
- `core/geolocation_utils.py` - Geofencing logic
- `core/models.py` - GPS fields (latitude, longitude, geofence_radius_meters)

---

### 2. 🖼️ **Image Similarity Scanning (CLIP Embeddings)**
**How it works:**
- Museum staff uploads high-quality artwork images
- AI generates 512-dimensional vector embeddings (when CLIP is enabled)
- Visitor points camera at artwork
- App captures frame and generates embedding
- Compares visitor's embedding with database using cosine similarity
- Returns best match if similarity > threshold

**Use case:** Identifies which specific artwork the visitor is viewing

**Files:**
- `embeddings/engine.py` - CLIP model and similarity search
- `core/models.py` - Vector embedding fields
- `embeddings/tasks.py` - Async embedding generation

**Status:** ⚠️ Currently disabled due to memory limits on Render free tier

---

## 🚫 **Removed Technologies**

### ❌ QR Code Scanning
**Why removed:** User requested location + image similarity only
- No QR code generation
- No QR code storage
- Cleaner user experience

---

## 💡 **Current Architecture**

### **Workflow:**
1. **Museum Staff:**
   - Uploads artwork image
   - GPS coordinates auto-captured
   - Artwork description (English)
   - Auto-translated to 14 languages
   - Audio narration generated

2. **Visitor Experience:**
   - Opens camera in browser
   - Points at artwork
   - **Step 1:** Geofence check (are they in the museum?)
   - **Step 2:** Image similarity match (which artwork?)
   - Shows AR description overlay
   - Language selector (14 options)
   - Audio narration plays

---

## 🔧 **To Enable Full Image Similarity:**

### **Requirements:**
- Upgrade Render plan to 2GB+ RAM
- Uncomment in `requirements.txt`:
  ```
  torch==2.5.1
  torchvision==0.20.1
  sentence-transformers==2.2.2
  git+https://github.com/openai/CLIP.git
  ```
- Push to GitHub
- Run migrations on Render

### **Cost:**
- Render Starter Plan: $7/month (512MB RAM) - May still crash
- Render Standard Plan: $25/month (2GB RAM) - Recommended

---

## ✅ **Current Status:**

**Working Features:**
- ✅ Geofencing (location-based access)
- ✅ Camera scanning (UI ready)
- ✅ Auto-translation (14 languages)
- ✅ Text-to-speech
- ✅ AR description overlay
- ✅ Museum staff dashboard

**Pending (needs paid plan):**
- ⏳ AI image similarity matching
- ⏳ Vector embeddings
- ⏳ "Find similar artworks" feature

---

## 🎨 **Scanner Templates:**

1. **`templates/scanner.html`** - Basic scanner
2. **`templates/scanner_advanced.html`** - AR scanner with:
   - Language selector
   - Geofence validation
   - AR description overlay
   - Capture button (locks view)
   - Audio playback

---

## 📊 **Database Schema:**

```python
class Artwork(models.Model):
    # Location-based
    latitude = DecimalField()  # GPS coordinates
    longitude = DecimalField()
    geofence_radius_meters = IntegerField(default=100)
    
    # Image-based (optional - needs CLIP)
    image = ImageField()
    embedding = VectorField(dimensions=512, null=True)  # CLIP vector
    
    # No QR code field (removed)
```

---

## 🚀 **Recommendation:**

**For now (free tier):**
- Use **geofencing only**
- Visitor enters museum → scans artwork → description shown
- Works perfectly without AI

**For future (paid tier):**
- Enable **CLIP embeddings**
- Precise artwork matching by image content
- "Find similar artworks" recommendations
- Better visitor experience

Your app is production-ready with geofencing! 🎉
