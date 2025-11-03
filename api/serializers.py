"""
DRF Serializers for ArtScope API
"""
from rest_framework import serializers
from core.models import (
    Museum, Artist, Artwork, VisitorSession, 
    ArtworkInteraction, VisitorFeedback
)


class MuseumSerializer(serializers.ModelSerializer):
    """Museum serializer with artwork count"""
    
    artwork_count = serializers.IntegerField(source='artworks.count', read_only=True)
    
    class Meta:
        model = Museum
        fields = [
            'id', 'name', 'description', 'location', 'contact_email',
            'website', 'logo', 'artwork_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ArtistSerializer(serializers.ModelSerializer):
    """Artist serializer"""
    
    class Meta:
        model = Artist
        fields = [
            'id', 'name', 'birth_year', 'death_year', 'nationality',
            'biography', 'style', 'movement'
        ]
        read_only_fields = ['id']


class ArtworkListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for artwork lists"""
    
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    museum_name = serializers.CharField(source='museum.name', read_only=True)
    
    class Meta:
        model = Artwork
        fields = [
            'id', 'title', 'artist_name', 'museum_name', 'category',
            'year_created', 'image', 'scan_count', 'is_on_display'
        ]


class ArtworkDetailSerializer(serializers.ModelSerializer):
    """Detailed artwork serializer with all media"""
    
    artist = ArtistSerializer(read_only=True)
    museum = MuseumSerializer(read_only=True)
    
    class Meta:
        model = Artwork
        fields = [
            'id', 'museum', 'artist', 'title', 'description', 'year_created',
            'category', 'medium', 'dimensions', 'gallery_location', 'room_number',
            'image', 'video_360', 'audio_narration', 'tags', 'historical_context',
            'provenance', 'acquisition_date', 'scan_count', 'view_count',
            'avg_dwell_time_seconds', 'is_on_display', 'created_at'
        ]
        read_only_fields = ['id', 'scan_count', 'view_count', 'avg_dwell_time_seconds', 'created_at']


class ArtworkCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating artworks"""
    
    class Meta:
        model = Artwork
        fields = [
            'museum', 'artist', 'title', 'description', 'year_created',
            'category', 'medium', 'dimensions', 'gallery_location', 'room_number',
            'image', 'video_360', 'audio_narration', 'tags', 'historical_context',
            'provenance', 'acquisition_date', 'is_on_display'
        ]


class ScanRequestSerializer(serializers.Serializer):
    """Serializer for artwork scan requests"""
    
    image = serializers.ImageField(required=True)
    museum_id = serializers.UUIDField(required=True)
    session_id = serializers.UUIDField(required=False, allow_null=True)


class ScanResultSerializer(serializers.Serializer):
    """Serializer for scan results"""
    
    artwork = ArtworkDetailSerializer()
    similarity_score = serializers.FloatField()
    session_id = serializers.UUIDField()
    recommendations = ArtworkListSerializer(many=True)


class VisitorSessionSerializer(serializers.ModelSerializer):
    """Visitor session serializer"""
    
    class Meta:
        model = VisitorSession
        fields = [
            'id', 'museum', 'session_start', 'session_end', 'duration_seconds',
            'artworks_scanned', 'total_interactions', 'analytics_consent', 'opted_out'
        ]
        read_only_fields = ['id', 'session_start']


class ArtworkInteractionSerializer(serializers.ModelSerializer):
    """Artwork interaction serializer"""
    
    artwork_title = serializers.CharField(source='artwork.title', read_only=True)
    
    class Meta:
        model = ArtworkInteraction
        fields = [
            'id', 'session', 'artwork', 'artwork_title', 'interaction_type',
            'timestamp', 'dwell_time_seconds', 'similarity_score'
        ]
        read_only_fields = ['id', 'timestamp']


class VisitorFeedbackSerializer(serializers.ModelSerializer):
    """Visitor feedback serializer"""
    
    class Meta:
        model = VisitorFeedback
        fields = [
            'id', 'session', 'artwork', 'reaction', 'comment', 'sentiment_score', 'created_at'
        ]
        read_only_fields = ['id', 'sentiment_score', 'created_at']


class AnalyticsSummarySerializer(serializers.Serializer):
    """Serializer for analytics summary"""
    
    museum_name = serializers.CharField()
    period_days = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    total_interactions = serializers.IntegerField()
    avg_session_duration_minutes = serializers.FloatField()
    avg_dwell_time_seconds = serializers.FloatField()
    top_artworks = serializers.ListField()
    interaction_breakdown = serializers.ListField()
    daily_trends = serializers.ListField()


class RecommendationSerializer(serializers.Serializer):
    """Serializer for artwork recommendations"""
    
    artwork = ArtworkListSerializer()
    score = serializers.FloatField()
    reason = serializers.CharField()
