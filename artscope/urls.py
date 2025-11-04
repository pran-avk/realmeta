"""
ArtScope URL Configuration
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.views import (
    register_view, login_view, logout_view, dashboard_view,
    upload_artwork_view, upload_artwork_submit, delete_artwork_view, edit_artwork_view,
    record_navigation_path_view, visitor_navigation_view,
    upload_floor_map_view, museum_map_view
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('api.urls')),
    
    # Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Museum Staff Authentication
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Artwork Upload
    path('upload-artwork/', upload_artwork_view, name='upload_artwork'),
    path('upload-artwork/submit/', upload_artwork_submit, name='upload_artwork_submit'),
    
    # Artwork Management
    path('edit-artwork/<uuid:artwork_id>/', edit_artwork_view, name='edit_artwork'),
    path('delete-artwork/<uuid:artwork_id>/', delete_artwork_view, name='delete_artwork'),
    
    # Navigation System
    path('record-navigation/', record_navigation_path_view, name='record_navigation_path'),
    path('navigate/', visitor_navigation_view, name='visitor_navigation'),
    
    # Floor Maps
    path('upload-floor-map/', upload_floor_map_view, name='upload_floor_map'),
    path('museum-map/', museum_map_view, name='museum_map'),
    
    # Frontend Templates (No map requirement)
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('scanner/', TemplateView.as_view(template_name='scanner.html'), name='scanner'),
    path('scanner-ai/', TemplateView.as_view(template_name='scanner_client_side.html'), name='scanner_ai'),
    path('artwork-details/', TemplateView.as_view(template_name='artwork_details.html'), name='artwork_details'),
]

# Serve media files in both development AND production
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin configuration
admin.site.site_header = "ArtScope Admin"
admin.site.site_title = "ArtScope Administration"
admin.site.index_title = "Museum & Artwork Management"
