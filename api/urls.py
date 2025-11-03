"""
API URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MuseumViewSet, ArtistViewSet, ArtworkViewSet,
    scan_artwork, log_interaction, submit_feedback,
    get_recommendations, opt_out_analytics, health_check
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'museums', MuseumViewSet, basename='museum')
router.register(r'artists', ArtistViewSet, basename='artist')
router.register(r'artworks', ArtworkViewSet, basename='artwork')

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # Core AR scanning endpoint (anonymous)
    path('scan/', scan_artwork, name='scan-artwork'),
    
    # Analytics endpoints (anonymous)
    path('interactions/', log_interaction, name='log-interaction'),
    path('feedback/', submit_feedback, name='submit-feedback'),
    path('recommendations/', get_recommendations, name='get-recommendations'),
    
    # Privacy endpoint
    path('opt-out/', opt_out_analytics, name='opt-out-analytics'),
    
    # Health check
    path('health/', health_check, name='health-check'),
]
