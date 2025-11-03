# 🎨 ArtScope Frontend Setup Guide

## Overview
Three beautiful, mobile-optimized HTML templates with **native camera integration** (no AR.js or Three.js libraries needed - uses native WebRTC).

## 📱 Templates Created

### 1. **index.html** - Welcome Screen
- Beautiful gradient background
- Privacy consent section
- Session creation flow
- No account needed messaging

### 2. **scanner.html** - AR Camera Scanner
- **Native camera access** using WebRTC (`getUserMedia`)
- Real-time camera feed
- Animated scanning frame with corner markers
- Capture and upload to backend API
- Bottom navigation bar (map removed per your request)

### 3. **artwork_details.html** - Artwork Display
- Full artwork information
- Stats display (match score, scans, views)
- Audio guide integration
- 360° video player support
- Sentiment feedback system
- Personalized recommendations carousel
- Share and save functionality

## 🚀 Quick Start

### Step 1: Templates are Ready!
All templates are in `c:\Users\kp755\OneDrive\Desktop\RealMeta\templates\`

### Step 2: URL Routes Configured
Updated `artscope/urls.py` with template views:
```python
path('', TemplateView.as_view(template_name='index.html'), name='home'),
path('scanner/', TemplateView.as_view(template_name='scanner.html'), name='scanner'),
path('artwork-details/', TemplateView.as_view(template_name='artwork_details.html'), name='artwork_details'),
```

### Step 3: Django Settings Updated
Templates directory configured in `settings.py`:
```python
'DIRS': [BASE_DIR / 'templates'],
```

## 🎥 How Camera Scanning Works

### Technology Used
- **WebRTC API** - Native browser camera access (no libraries needed)
- **Canvas API** - Image capture and conversion
- **FormData API** - Binary image upload to backend

### Camera Flow
1. User lands on welcome page → clicks "Start Scanning"
2. Scanner page requests camera permissions via `navigator.mediaDevices.getUserMedia()`
3. Live camera feed displays with scanning frame overlay
4. User taps capture button → frame captured to canvas → converted to JPEG blob
5. Image uploaded to `/api/scan/` endpoint via FormData POST
6. Backend processes with CLIP embeddings → returns artwork match
7. Redirects to artwork details page with full information

### Code Snippet (scanner.html)
```javascript
// Request camera with environment (rear) camera preference
stream = await navigator.mediaDevices.getUserMedia({
    video: {
        facingMode: 'environment',  // Use back camera on mobile
        width: { ideal: 1920 },
        height: { ideal: 1080 }
    }
});

// Capture frame
canvas.width = video.videoWidth;
canvas.height = video.videoHeight;
ctx.drawImage(video, 0, 0);

// Upload to backend
canvas.toBlob(async (blob) => {
    const formData = new FormData();
    formData.append('image', blob, 'scan.jpg');
    
    const response = await fetch('/api/scan/', {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    // Display artwork details
}, 'image/jpeg', 0.9);
```

## 📲 Mobile Optimization

### Responsive Features
- Viewport meta tag for proper mobile scaling
- Touch-optimized buttons (48px minimum tap targets)
- Backdrop blur effects with fallbacks
- Smooth animations (GPU accelerated)
- Overflow scroll for recommendations
- Bottom navigation bar (iOS safe area compatible)

### Camera Permissions
**iOS Safari:**
- Requires HTTPS in production
- User must explicitly allow camera access
- Works on iOS 14.3+

**Android Chrome:**
- Camera access prompt on first use
- Works on Android 5.0+ (Lollipop)

## 🎨 Design Features Matching Reference Image

### Welcome Screen
✅ Dark gradient background (#1a1a2e → #16213e)  
✅ Museum lighting hero image placeholder  
✅ "Welcome to the Gallery Guide" heading  
✅ Privacy consent section with checkmarks  
✅ "Start Scanning" primary button  
✅ "Accept & Continue" secondary button  

### Scanner Screen
✅ Full-screen camera view  
✅ Scanning frame with animated corners  
✅ "Point your camera at a painting" instruction  
✅ Scanning status spinner  
✅ Bottom navigation (Scan / Capture / Help)  
✅ Close button top-right  

### Artwork Details
✅ Large artwork image at top  
✅ Title, artist, year display  
✅ Match score percentage  
✅ Audio guide & 360° video buttons  
✅ Description and historical context  
✅ Reaction feedback (❤️ 👍 😐 👎)  
✅ Recommendation carousel  
✅ Share and save buttons  

## 🔧 Customization

### Change Colors
Edit the CSS gradient in each template:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Add Your Logo
Replace emoji in `index.html` hero section:
```html
<div class="hero-icon">🎨</div>
<!-- Change to: -->
<img src="/static/images/logo.png" alt="Logo">
```

### Adjust Camera Quality
In `scanner.html`, modify video constraints:
```javascript
video: {
    facingMode: 'environment',
    width: { ideal: 3840 },  // 4K resolution
    height: { ideal: 2160 }
}
```

## 📡 API Integration

### Frontend → Backend Communication

**1. Create Session (index.html)**
```javascript
POST /api/sessions/
Body: { "analytics_consent": true }
Response: { "id": "uuid", "created_at": "..." }
```

**2. Scan Artwork (scanner.html)**
```javascript
POST /api/scan/
Body: FormData with 'image' file and 'session_id'
Response: {
    "artwork": { "id": 1, "title": "...", "artist": {...} },
    "similarity_score": 0.95,
    "recommendations": [...]
}
```

**3. Submit Feedback (artwork_details.html)**
```javascript
POST /api/feedback/
Body: {
    "session": "uuid",
    "artwork": 1,
    "reaction": "love",
    "comment": "Beautiful!"
}
```

**4. Log Interaction**
```javascript
POST /api/interactions/
Body: {
    "session": "uuid",
    "artwork": 1,
    "interaction_type": "view_details",
    "dwell_time_seconds": 30
}
```

## 🚀 Testing Locally

### 1. Start Django Server
```powershell
cd c:\Users\kp755\OneDrive\Desktop\RealMeta
python manage.py runserver
```

### 2. Access Pages
- Welcome: http://localhost:8000/
- Scanner: http://localhost:8000/scanner/
- Details: http://localhost:8000/artwork-details/

### 3. Test Camera
**Desktop:** Use built-in webcam  
**Mobile:** Use ngrok for HTTPS testing:
```powershell
ngrok http 8000
```
Then access via the HTTPS URL on your phone

## 🎯 Features Removed (Per Your Request)

❌ **Museum Map** - Navigation removed from scanner bottom bar  
❌ **AR.js Library** - Using native WebRTC instead  
❌ **Three.js** - Not needed for 2D scanning  
❌ **React** - Pure HTML/CSS/JS (faster, no build process)  

## ✨ Enhanced Features Added

### 1. **Session Persistence**
Uses `sessionStorage` to maintain visitor session across pages:
```javascript
sessionStorage.setItem('artscope_session_id', data.id);
sessionStorage.setItem('scanned_artwork', JSON.stringify(data));
```

### 2. **Privacy-First Design**
- No login required
- Anonymous UUID sessions
- Consent collection on welcome page
- Data retention settings in admin

### 3. **Progressive Enhancement**
- Works without JavaScript (basic navigation)
- Camera fallback error messages
- Share API with fallback

### 4. **Performance Optimizations**
- CSS animations use `transform` (GPU accelerated)
- Images lazy load
- Backdrop blur with fallback
- Debounced API calls

## 📱 Production Deployment

### HTTPS Required
Camera access requires HTTPS in production. Render provides this automatically.

### Environment Variables
Already configured in your backend:
```
ALLOWED_HOSTS=artscope.render.com,localhost
CORS_ALLOWED_ORIGINS=https://artscope.render.com
```

### Static Files
Whitenoise serves templates in production automatically.

## 🐛 Troubleshooting

### Camera Not Working
**Issue:** Black screen or permission denied  
**Fix:** Ensure HTTPS in production, check browser permissions

### Templates Not Found
**Issue:** TemplateDoesNotExist error  
**Fix:** Check `TEMPLATES['DIRS']` in settings.py points to templates folder

### CORS Errors
**Issue:** API calls blocked  
**Fix:** Verify `CORS_ALLOWED_ORIGINS` includes your domain

### Image Upload Fails
**Issue:** 413 Request Entity Too Large  
**Fix:** Reduce JPEG quality in scanner.html (currently 0.9, try 0.7)

## 📚 File Structure

```
RealMeta/
├── templates/
│   ├── index.html              # Welcome & consent
│   ├── scanner.html            # Camera scanning
│   └── artwork_details.html    # Artwork display
├── artscope/
│   ├── settings.py             # Templates config added
│   └── urls.py                 # Template routes added
└── requirements.txt            # All dependencies included
```

## 🎓 Next Steps

1. ✅ Templates created and configured
2. ✅ URL routes added
3. ✅ Settings updated
4. 🔄 Run migrations: `python manage.py migrate`
5. 🔄 Create superuser: `python manage.py createsuperuser`
6. 🔄 Upload sample artworks via admin
7. 🔄 Test scanning flow end-to-end
8. 🔄 Deploy to Render with HTTPS

## 💡 Advanced Features (Optional)

### Add AR.js for Marker-Based Tracking
If you want true AR with 3D models later:
```html
<script src="https://cdn.jsdelivr.net/gh/aframevr/aframe@1.4.0/dist/aframe-master.min.js"></script>
<script src="https://raw.githack.com/AR-js-org/AR.js/master/aframe/build/aframe-ar.js"></script>
```

### Add Three.js for 3D Artwork Viewer
For rotating 3D models of sculptures:
```html
<script src="https://cdn.jsdelivr.net/npm/three@0.159.0/build/three.min.js"></script>
```

### Add React for Complex UI
Convert templates to React components if needed for state management.

---

**Your frontend is ready! 🎉**  
Pure HTML/CSS/JS with native camera access, no complex libraries needed.
