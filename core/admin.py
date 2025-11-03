"""
Django Admin Configuration for ArtScope
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Museum, MuseumStaff, Artist, Artwork, 
    VisitorSession, ArtworkInteraction, VisitorFeedback,
    CachedEmbedding, SystemLog
)


@admin.register(Museum)
class MuseumAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'is_active', 'analytics_enabled', 'created_at']
    list_filter = ['is_active', 'analytics_enabled', 'created_at']
    search_fields = ['name', 'location']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(MuseumStaff)
class MuseumStaffAdmin(admin.ModelAdmin):
    list_display = ['username', 'get_full_name', 'museum', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'museum']
    search_fields = ['username', 'first_name', 'last_name', 'email']


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ['name', 'birth_year', 'death_year', 'nationality', 'style']
    list_filter = ['nationality', 'style', 'movement']
    search_fields = ['name', 'biography']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'museum', 'category', 'is_on_display', 'scan_count', 'view_count']
    list_filter = ['category', 'is_on_display', 'museum', 'created_at']
    search_fields = ['title', 'description', 'artist__name']
    readonly_fields = ['id', 'embedding_generated_at', 'created_at', 'updated_at', 'scan_count', 'view_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('museum', 'artist', 'title', 'description', 'year_created', 'category', 'medium', 'dimensions')
        }),
        ('Location', {
            'fields': ('gallery_location', 'room_number')
        }),
        ('Media Files', {
            'fields': ('image', 'video_360', 'audio_narration')
        }),
        ('Embedding', {
            'fields': ('embedding_model', 'embedding_generated_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('tags', 'historical_context', 'provenance', 'acquisition_date'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('scan_count', 'view_count', 'avg_dwell_time_seconds'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_on_display', 'created_at', 'updated_at')
        }),
    )


@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'museum', 'session_start', 'duration_seconds', 'artworks_scanned', 'opted_out']
    list_filter = ['museum', 'opted_out', 'session_start']
    readonly_fields = ['id', 'session_start']
    search_fields = ['id']


@admin.register(ArtworkInteraction)
class ArtworkInteractionAdmin(admin.ModelAdmin):
    list_display = ['artwork', 'interaction_type', 'timestamp', 'dwell_time_seconds', 'similarity_score']
    list_filter = ['interaction_type', 'timestamp']
    readonly_fields = ['id', 'timestamp']
    search_fields = ['artwork__title']


@admin.register(VisitorFeedback)
class VisitorFeedbackAdmin(admin.ModelAdmin):
    list_display = ['artwork', 'reaction', 'sentiment_score', 'created_at']
    list_filter = ['reaction', 'created_at']
    readonly_fields = ['id', 'created_at', 'sentiment_score']
    search_fields = ['artwork__title', 'comment']


@admin.register(CachedEmbedding)
class CachedEmbeddingAdmin(admin.ModelAdmin):
    list_display = ['artwork', 'access_count', 'last_accessed']
    readonly_fields = ['created_at', 'last_accessed']


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['log_type', 'message_short', 'created_at']
    list_filter = ['log_type', 'created_at']
    readonly_fields = ['id', 'created_at']
    search_fields = ['message']
    
    def message_short(self, obj):
        return obj.message[:100] if len(obj.message) > 100 else obj.message
    message_short.short_description = 'Message'
