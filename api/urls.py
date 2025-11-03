"""
API URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MuseumViewSet, ArtistViewSet, ArtworkViewSet, VisitorSessionViewSet,
    scan_artwork, scan_artwork_combined, log_interaction, submit_feedback,
    get_recommendations, opt_out_analytics, health_check, check_geofence_access,
    save_navigation_path, get_navigation_path, get_nearest_waypoint
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'museums', MuseumViewSet, basename='museum')
router.register(r'artists', ArtistViewSet, basename='artist')
router.register(r'artworks', ArtworkViewSet, basename='artwork')
router.register(r'sessions', VisitorSessionViewSet, basename='session')

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # Primary scanning method: Geofencing (location-based)
    path('geofence/check/', check_geofence_access, name='check-geofence'),
    
    # Combined scanning: Geofencing + Image Recognition (RECOMMENDED)
    path('scan/combined/', scan_artwork_combined, name='scan-combined'),
    
    # Legacy AR scanning endpoint (image only)
    path('scan/', scan_artwork, name='scan-artwork'),
    
    # Analytics endpoints (anonymous)
    path('interactions/', log_interaction, name='log-interaction'),
    path('feedback/', submit_feedback, name='submit-feedback'),
    path('recommendations/', get_recommendations, name='get-recommendations'),
    
    # Privacy endpoint
    path('opt-out/', opt_out_analytics, name='opt-out-analytics'),
    
    # Navigation endpoints
    path('navigation/paths/', save_navigation_path, name='save-navigation-path'),
    path('navigation/path/', get_navigation_path, name='get-navigation-path'),
    path('navigation/waypoints/nearest/', get_nearest_waypoint, name='get-nearest-waypoint'),
    
    # Health check
    path('health/', health_check, name='health-check'),
]
