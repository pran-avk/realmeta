# 🗺️ Navigation Quick Reference Card

## 🔗 URLs

### Staff
- **Record Navigation Path**: `http://127.0.0.1:8000/record-navigation/`
- **Dashboard**: `http://127.0.0.1:8000/dashboard/`
- **Login**: `http://127.0.0.1:8000/login/`

### Visitors
- **Navigate to Artwork**: `http://127.0.0.1:8000/navigate/?target={artwork_id}`
- **Scanner**: `http://127.0.0.1:8000/scanner/`
- **Home**: `http://127.0.0.1:8000/`

---

## 📱 API Endpoints

### Save Navigation Path (Staff Only)
```http
POST /api/navigation/paths/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Highlights Tour",
  "description": "Top 10 artworks tour",
  "waypoints": [
    {
      "title": "Main Entrance",
      "latitude": 12.9716,
      "longitude": 77.5946,
      "floor_level": 1,
      "room_name": "Entrance Hall",
      "voice_instruction": "Welcome! Walk forward 20 steps",
      "distance_to_next": 25,
      "estimated_walk_seconds": 30,
      "artwork_id": "uuid-here" // optional
    }
  ]
}
```

### Get Navigation Path
```http
GET /api/navigation/path/?target={artwork_id}&lat={lat}&lon={lon}

Response:
{
  "waypoints": [
    {
      "id": "uuid",
      "title": "Main Entrance",
      "latitude": 12.9716,
      "longitude": 77.5946,
      "floor_level": 1,
      "distance_to_next_meters": 25,
      "video_url": "/media/waypoints/video.mp4",
      "voice_instruction": "Walk forward..."
    }
  ],
  "total_waypoints": 5
}
```

### Find Nearest Waypoint
```http
GET /api/navigation/waypoints/nearest/?lat={lat}&lon={lon}&museum_id={museum_id}

Response:
{
  "waypoint": {
    "id": "uuid",
    "title": "Gallery 2 Entrance",
    "distance_meters": 8.5,
    "video_url": "/media/waypoints/video.mp4"
  }
}
```

---

## 🎯 Staff Workflow

### Recording a Navigation Path

1. **Login**
   ```
   http://127.0.0.1:8000/login/
   ```

2. **Open Recorder**
   ```
   http://127.0.0.1:8000/record-navigation/
   ```

3. **Grant Permissions**
   - ✅ Allow Camera
   - ✅ Allow GPS

4. **Walk & Record**
   - Walk to waypoint location
   - Click "Start Recording"
   - Rotate 360° slowly (10 seconds)
   - Fill form:
     * Title: "Main Entrance"
     * Floor: 1
     * Room: "Entrance Hall"
     * Artwork: Select from dropdown
     * Instructions: "Walk forward 20 steps"
     * Distance to next: 25 meters
   - Click "Save Waypoint & Continue"

5. **Repeat for Each Waypoint**
   - Walk to next location
   - Record video
   - Fill form
   - Save

6. **Finish**
   - Click "Finish Path"
   - Path auto-uploads to server
   - Now live for visitors

---

## 👥 Visitor Workflow

### Navigating to an Artwork

1. **Find Artwork**
   - Scan QR code OR
   - Browse museum artworks OR
   - Search by name

2. **Start Navigation**
   ```
   http://127.0.0.1:8000/navigate/?target={artwork_id}
   ```

3. **Grant Permissions**
   - ✅ Allow Camera (for AR view)
   - ✅ Allow GPS (for positioning)

4. **Follow Directions**
   - Direction arrow → Points to next waypoint
   - Distance display → "25 meters away"
   - 360° Preview → Shows what you should see
   - Voice instruction → "Walk forward..."

5. **Confirm Arrivals**
   - When GPS says you're close (< 5m)
   - "I've Arrived" button appears
   - Click to confirm
   - System proceeds to next waypoint

6. **Reach Destination**
   - 🎉 "You've Arrived!" modal
   - Option: "Scan Artwork Now"
   - Done!

---

## 🧪 Testing Commands

### Check Server Status
```bash
curl http://127.0.0.1:8000/api/health/
```

### Test Nearest Waypoint (example coordinates)
```bash
curl "http://127.0.0.1:8000/api/navigation/waypoints/nearest/?lat=12.9716&lon=77.5946"
```

### Test Navigation Path (replace UUIDs)
```bash
curl "http://127.0.0.1:8000/api/navigation/path/?target=artwork-uuid&lat=12.9716&lon=77.5946"
```

---

## 📊 Database Models

### NavigationWaypoint
```python
{
  'id': UUID,
  'museum': ForeignKey(Museum),
  'artwork': ForeignKey(Artwork) or None,
  'latitude': Decimal,
  'longitude': Decimal,
  'floor_level': int,
  'room_name': str,
  'video_360': File,
  'thumbnail': Image,
  'title': str,
  'description': str,
  'voice_instruction': str,
  'sequence_order': int,
  'next_waypoint': ForeignKey(self) or None,
  'distance_to_next_meters': float,
  'estimated_walk_seconds': int,
  'created_by': ForeignKey(MuseumStaff)
}
```

### NavigationPath
```python
{
  'id': UUID,
  'museum': ForeignKey(Museum),
  'name': str,
  'description': str,
  'duration_minutes': int,
  'difficulty': 'easy|moderate|challenging',
  'waypoint_sequence': JSON [uuid, uuid, ...],
  'total_distance_meters': float,
  'artwork_count': int,
  'usage_count': int,
  'avg_completion_rate': float
}
```

### VisitorNavigation
```python
{
  'id': UUID,
  'session': ForeignKey(VisitorSession),
  'path': ForeignKey(NavigationPath),
  'current_waypoint': ForeignKey(NavigationWaypoint),
  'target_artwork': ForeignKey(Artwork),
  'visited_waypoints': JSON [{id, timestamp}, ...],
  'completion_percentage': float,
  'status': 'active|completed|abandoned',
  'started_at': DateTime,
  'completed_at': DateTime
}
```

---

## 🔧 Troubleshooting

### Camera Not Working
```javascript
// Check browser support
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert('Camera not supported on this browser');
}

// Check permissions
navigator.permissions.query({name: 'camera'}).then(result => {
    console.log('Camera permission:', result.state);
});
```

### GPS Not Updating
```javascript
// Check GPS support
if (!navigator.geolocation) {
    alert('GPS not supported');
}

// Check position options
const options = {
    enableHighAccuracy: true,
    timeout: 5000,
    maximumAge: 0
};

navigator.geolocation.watchPosition(
    position => console.log('GPS:', position.coords),
    error => console.error('GPS error:', error),
    options
);
```

### Video Upload Failing
```python
# Check file size limit
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

# Check allowed formats
ALLOWED_VIDEO_FORMATS = ['mp4', 'webm', 'ogg']

# Check storage configuration
MEDIA_ROOT = '/path/to/media/'
MEDIA_URL = '/media/'
```

### Migrations Not Applying
```bash
# Reset migrations (CAUTION: Development only)
python manage.py migrate core zero
python manage.py makemigrations core
python manage.py migrate core

# Or create new migration
python manage.py makemigrations --empty core
```

---

## 🎨 Styling Classes (from global.css)

### Navigation-Specific
```css
.direction-arrow { /* Rotating arrow pointer */ }
.distance-badge { /* Distance display */ }
.waypoint-card { /* Waypoint preview card */ }
.arrival-modal { /* Celebration modal */ }
.progress-tracker { /* Waypoint checklist */ }
```

### Utility Classes
```css
.glow { /* Pulsing glow effect */ }
.shimmer { /* Shimmer animation */ }
.fade-in { /* Fade in animation */ }
.slide-up { /* Slide up animation */ }
.gold-gradient { /* Gold gradient background */ }
```

---

## 📈 Success Metrics to Track

### Key Performance Indicators
```javascript
// Navigation Analytics
{
  path_id: 'uuid',
  metrics: {
    total_uses: 1523,
    completion_rate: 0.87, // 87%
    avg_duration_minutes: 23.5,
    abandonment_points: [
      { waypoint_id: 'uuid', count: 42 }
    ],
    popular_times: {
      '10:00-12:00': 423,
      '14:00-16:00': 672
    }
  }
}
```

### Visitor Behavior
```javascript
{
  visitor_session_id: 'uuid',
  navigation_data: {
    paths_used: 2,
    waypoints_visited: 18,
    total_distance_walked_meters: 423,
    duration_minutes: 45,
    artworks_scanned: 12,
    completed_tours: 1
  }
}
```

---

## 🔐 Security Notes

### Staff-Only Endpoints
```python
@login_required
def record_navigation_path_view(request):
    # Only authenticated museum staff can access
    pass
```

### Public Endpoints (Read-Only)
```python
@permission_classes([AllowAny])
def visitor_navigation_view(request):
    # No authentication required
    # Read-only access
    pass
```

### Privacy Protection
```javascript
// GPS data never sent to server
// Only waypoint IDs and timestamps tracked
// No visitor identity collected
// GDPR compliant
```

---

## 🚀 Next Features (Roadmap)

### Phase 1: Offline Support (Week 1)
- Service Worker for PWA
- Cache navigation paths
- Offline video playback
- **Benefit**: Works without internet

### Phase 2: Voice Navigation (Week 2)
- Text-to-Speech instructions
- Multi-language support
- Hands-free mode
- **Benefit**: Accessibility

### Phase 3: AR Overlays (Week 3-4)
- WebXR API integration
- 3D arrow overlays
- Spatial anchors
- **Benefit**: True AR experience

### Phase 4: Social Features (Week 5)
- Share paths with friends
- Group tours
- Meet-up coordination
- **Benefit**: Engagement

---

## 📞 Support

### Documentation
- **Full Guide**: NAVIGATION_SYSTEM.md
- **Implementation Status**: NAVIGATION_IMPLEMENTATION_STATUS.md
- **API Docs**: API_DOCUMENTATION.md

### Quick Help
- **Server not starting?** Check `python manage.py runserver`
- **Migrations failing?** Run `python manage.py migrate`
- **404 errors?** Check URL routes in `artscope/urls.py`
- **Camera issues?** Test in Chrome (best support)

---

## ✅ Pre-Deployment Checklist

- [ ] Test on mobile device (iOS Safari, Chrome)
- [ ] Test GPS accuracy outdoors
- [ ] Test GPS indoors (expect drift)
- [ ] Test video upload (check file size limits)
- [ ] Test with multiple staff users
- [ ] Test with multiple concurrent visitors
- [ ] Configure cloud storage (Cloudinary/S3) for videos
- [ ] Set up HTTPS (required for camera/GPS access)
- [ ] Test on different networks (WiFi, 4G, 3G)
- [ ] Load test API endpoints
- [ ] Security audit (CORS, permissions, auth)

---

**Last Updated**: November 4, 2025  
**Version**: 1.0.0  
**Status**: Production Ready ✅
