"""
ArtScope URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('api.urls')),
    
    # Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Frontend Templates (No map requirement)
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('scanner/', TemplateView.as_view(template_name='scanner.html'), name='scanner'),
    path('artwork-details/', TemplateView.as_view(template_name='artwork_details.html'), name='artwork_details'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin configuration
admin.site.site_header = "ArtScope Admin"
admin.site.site_title = "ArtScope Administration"
admin.site.index_title = "Museum & Artwork Management"
