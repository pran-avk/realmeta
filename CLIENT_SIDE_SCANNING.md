# Client-Side Image Scanning with 3D Display

## 🎯 Overview

New AI-powered scanner that performs **client-side image similarity checking** with **3D text display** for artwork descriptions. This eliminates server-side processing and provides an immersive experience.

## 🚀 Key Features

### 1. **Location-Based Artwork Fetching**
- **API Endpoint**: `/api/scan/location-artworks/`
- **Method**: POST
- **Input**: GPS coordinates (latitude, longitude)
- **Output**: ALL artworks within geofence range with full data

```json
{
  "latitude": 40.7589,
  "longitude": -73.9851,
  "museum_id": "optional-uuid"
}
```

**Response**:
```json
{
  "success": true,
  "artworks": [
    {
      "id": "uuid",
      "title": "Starry Night",
      "artist_name": "Vincent van Gogh",
      "description": "Full description...",
      "image": "https://...",
      "distance_meters": 5.2
    }
  ],
  "count": 10,
  "message": "Found 10 artworks in your location"
}
```

### 2. **Client-Side Similarity Checking**
- **Algorithm**: Histogram-based color comparison
- **Process**:
  1. User scans artwork with camera
  2. Frontend downloads all nearby artwork images
  3. JavaScript computes histogram similarity
  4. Returns artwork with **maximum similarity score**
  5. **No "none" results** - always shows best match if exists

**Histogram Comparison**:
```javascript
// Computes 64-bin RGB histogram
// Compares using correlation
// Returns similarity score 0.0 to 1.0
```

**Advantages**:
- ✅ Works offline after data loaded
- ✅ No server processing overhead
- ✅ Real-time matching
- ✅ Always finds best match (max similarity)

### 3. **3D Text Display with Three.js**
- **Library**: Three.js r128
- **Features**:
  - Rotating 3D text plane with artwork details
  - Gold gradient background
  - Smooth animations
  - Auto-rotating display
  - Responsive to window resize

**Display Contents**:
- Artwork title (large, gold text)
- Artist name
- Description (wrapped, multi-line)
- Similarity score badge
- Close button to return to scanning

### 4. **Progressive Web Experience**
1. **Step 1**: User opens `/scanner-ai/`
2. **Step 2**: Camera initializes
3. **Step 3**: GPS location detected
4. **Step 4**: Server sends all nearby artworks to client
5. **Step 5**: User scans artwork
6. **Step 6**: Frontend compares with all artworks
7. **Step 7**: Best match displayed in 3D view

## 📁 Files Created/Modified

### New Files:
- `templates/scanner_client_side.html` - AI scanner with 3D view (800+ lines)

### Modified Files:
- `api/views.py` - Added `get_location_artworks()` endpoint
- `api/urls.py` - Added `/api/scan/location-artworks/` route
- `artscope/urls.py` - Added `/scanner-ai/` route
- `templates/index.html` - Added "AI Scanner (3D View)" button

## 🎨 User Interface

### Scanner Interface:
- **Camera feed**: Full-screen background
- **Scan frame**: Animated gold border with corner markers
- **Status messages**: Top center, shows location/loading status
- **Scan button**: Bottom center, 80px circular button

### 3D Result View:
- **Background**: Black with Three.js scene
- **3D Text**: Rotating plane with artwork details
- **Info panel**: Bottom center with title, artist, similarity
- **Close button**: Top right

## 🔧 Technical Details

### Image Comparison Algorithm:
```javascript
1. Compute RGB histogram (64 bins per channel)
2. Normalize histograms
3. Calculate correlation score
4. Return similarity (0.0 - 1.0)
```

### Geofencing:
- Uses existing `check_geofence()` utility
- Filters artworks by GPS proximity
- Only accessible artworks sent to client

### 3D Rendering:
- **Scene**: Black background
- **Camera**: Perspective FOV 75°
- **Lights**: Ambient + gold point light
- **Animation**: 60 FPS rotation loop

## 🚦 Usage

### For Visitors:
1. Go to homepage: `http://127.0.0.1:8000/`
2. Click **"🤖 AI Scanner (3D View)"** button
3. Allow camera and location access
4. Wait for "✅ X artworks found nearby!"
5. Point camera at artwork
6. Press **SCAN** button
7. View result in immersive 3D display

### For Museums:
- Upload artworks with GPS coordinates
- Set geofence radius (default 50m)
- Visitors within range will see artworks

## 📊 Comparison: Server-Side vs Client-Side

| Feature | Server-Side (`/api/scan/`) | Client-Side (`/scanner-ai/`) |
|---------|---------------------------|------------------------------|
| Processing | Backend (Python) | Frontend (JavaScript) |
| Speed | Network dependent | Instant after load |
| Offline | ❌ No | ✅ Yes (after data loaded) |
| Privacy | Image sent to server | Image stays local |
| Display | 2D list | 3D immersive view |
| Accuracy | High (deep learning) | Medium (histogram) |
| Best Match | Yes | **Always max similarity** |

## 🎯 Key Advantages

1. **No "None" Results**: Always shows the best match from available artworks
2. **Max Similarity**: Finds artwork with highest similarity score
3. **Immersive Display**: 3D rotating text with Three.js
4. **Privacy**: Scanned images never leave device
5. **Speed**: Instant comparison after data loaded
6. **Offline**: Works without internet after initial load
7. **Location-Aware**: Only shows nearby artworks

## 🌐 API Endpoints

### Get Location Artworks
```
POST /api/scan/location-artworks/
Content-Type: application/json

{
  "latitude": 40.7589,
  "longitude": -73.9851
}
```

### Classic Scan (server-side)
```
POST /api/scan/
Content-Type: multipart/form-data

image: <file>
```

### Combined Scan (geofence + server-side)
```
POST /api/scan/combined/
Content-Type: multipart/form-data

image: <file>
latitude: 40.7589
longitude: -73.9851
```

## 🔮 Future Enhancements

1. **Web Workers**: Move image processing to background thread
2. **IndexedDB**: Cache artwork data for true offline support
3. **TensorFlow.js**: Add deep learning for better accuracy
4. **AR.js**: Add augmented reality overlay
5. **WebGL Shaders**: Advanced 3D effects
6. **Voice Narration**: Audio description playback

## 📝 Notes

- Requires HTTPS for geolocation API (or localhost)
- Requires camera permission
- Three.js loaded from CDN (requires internet for first load)
- Works best with 5-20 artworks in location
- Similarity threshold: 30% minimum (0.30)

## 🎨 Screenshot Flow

```
1. Homepage
   ↓ Click "🤖 AI Scanner"
2. Camera View (with gold scan frame)
   ↓ GPS detected + artworks loaded
3. Status: "✅ 10 artworks found nearby!"
   ↓ Point at artwork + press SCAN
4. Status: "🔍 Analyzing image..."
   ↓ Client-side comparison
5. Status: "✅ Match found! 87% similar"
   ↓ Transition to 3D view
6. 3D Rotating Text Display
   - Title in gold
   - Artist name
   - Description
   - [87% Match] badge
   ↓ Click Close
7. Back to camera scan view
```

## 🏆 Achievement Unlocked!

✅ **Client-side image processing**
✅ **Location-based batch fetching**
✅ **3D immersive display**
✅ **Always shows best match (max similarity)**
✅ **No "none" results if artwork exists**
✅ **Privacy-first design**

---

**Server Status**: Running at `http://127.0.0.1:8000/`
**Test URL**: `http://127.0.0.1:8000/scanner-ai/`
