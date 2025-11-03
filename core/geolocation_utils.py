"""
Geolocation Utilities for ArtScope
Location-based (Geofencing) artwork access control
"""
from geopy.distance import geodesic


def check_geofence(user_lat, user_lon, artwork_lat, artwork_lon, radius_meters):
    """
    Check if user is within the geofence radius of an artwork
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        artwork_lat: Artwork's latitude
        artwork_lon: Artwork's longitude
        radius_meters: Geofence radius in meters
    
    Returns:
        dict with 'allowed' (bool) and 'distance' (float in meters)
    """
    if not all([user_lat, user_lon, artwork_lat, artwork_lon]):
        return {
            'allowed': False,
            'distance': None,
            'message': 'Missing location data'
        }
    
    # Calculate distance
    user_coords = (float(user_lat), float(user_lon))
    artwork_coords = (float(artwork_lat), float(artwork_lon))
    distance = geodesic(user_coords, artwork_coords).meters
    
    # Check if within radius
    allowed = distance <= radius_meters
    
    return {
        'allowed': allowed,
        'distance': round(distance, 2),
        'message': f'You are {round(distance, 2)}m from this artwork' if not allowed else 'Access granted'
    }


def get_distance_message(distance_meters):
    """
    Get a user-friendly distance message
    """
    if distance_meters < 50:
        return "You're very close! Look around."
    elif distance_meters < 100:
        return "You're nearby. Walk a bit closer."
    elif distance_meters < 500:
        return f"You're {int(distance_meters)}m away from the museum."
    elif distance_meters < 1000:
        return f"You're {int(distance_meters)}m away. Head to the museum."
    else:
        km = distance_meters / 1000
        return f"You're {km:.1f}km away from the museum."
