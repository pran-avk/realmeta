"""
Geolocation Utilities for ArtScope
Location-based (Geofencing) artwork access control - Optimized for speed
"""
from geopy.distance import geodesic


def check_geofence(user_lat, user_lon, artwork_lat, artwork_lon, radius_meters):
    """
    Check if user is within the geofence radius of an artwork
    OPTIMIZED: Returns tuple for fast processing
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        artwork_lat: Artwork's latitude
        artwork_lon: Artwork's longitude
        radius_meters: Geofence radius in meters
    
    Returns:
        tuple: (is_accessible: bool, distance_meters: float)
    """
    if not all([user_lat, user_lon, artwork_lat, artwork_lon]):
        return False, None
    
    # Calculate distance using geodesic (accurate for Earth's curvature)
    user_coords = (float(user_lat), float(user_lon))
    artwork_coords = (float(artwork_lat), float(artwork_lon))
    distance = geodesic(user_coords, artwork_coords).meters
    
    # Check if within radius
    is_accessible = distance <= radius_meters
    
    return is_accessible, distance


def get_distance_message(distance_meters, radius_meters):
    """
    Get a user-friendly distance message
    
    Args:
        distance_meters: Distance from artwork
        radius_meters: Geofence radius
    """
    if distance_meters <= radius_meters:
        return "✅ You're within range! Scan now."
    elif distance_meters < 50:
        return "📍 You're very close! Move a few more meters."
    elif distance_meters < 100:
        return f"🚶 Walk {int(distance_meters - radius_meters)}m closer to unlock."
    elif distance_meters < 500:
        return f"🏛️ You're {int(distance_meters)}m away. Head to the artwork."
    elif distance_meters < 1000:
        return f"🗺️ {int(distance_meters)}m away. Navigate to the museum."
    else:
        km = distance_meters / 1000
        return f"🌍 {km:.1f}km away. Visit the museum to scan."
