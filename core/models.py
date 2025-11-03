"""
Core Models for ArtScope
Advanced database models with vector embeddings, analytics, and privacy features
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.conf import settings
import uuid

# Conditionally import pgvector for PostgreSQL
try:
    from pgvector.django import VectorField
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False


class Museum(models.Model):
    """Museum entity with role-based access and analytics configuration"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255)
    contact_email = models.EmailField()
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='museums/logos/', blank=True, null=True)
    
    # Privacy & Analytics Settings
    analytics_enabled = models.BooleanField(default=True)
    data_retention_days = models.IntegerField(default=90)
    allow_visitor_feedback = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class MuseumStaff(AbstractUser):
    """Extended user model for museum staff with role-based access"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('curator', 'Curator'),
        ('staff', 'Staff Member'),
    ]
    
    museum = models.ForeignKey(Museum, on_delete=models.CASCADE, related_name='staff')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField(max_length=20, blank=True)
    
    # Fix: Add related_name to avoid clashes with default User model
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='museum_staff',
        blank=True,
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='museum_staff',
        blank=True,
        verbose_name='user permissions',
    )
    
    class Meta:
        verbose_name = 'Museum Staff'
        verbose_name_plural = 'Museum Staff'
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.museum.name}"


class Artist(models.Model):
    """Artist information with style vectors for recommendations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    birth_year = models.IntegerField(null=True, blank=True)
    death_year = models.IntegerField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    biography = models.TextField(blank=True)
    style = models.CharField(max_length=100, blank=True)
    movement = models.CharField(max_length=100, blank=True)
    
    # Style embedding for artist-based recommendations (PostgreSQL only)
    if VECTOR_AVAILABLE:
        style_embedding = VectorField(dimensions=512, null=True, blank=True)
    else:
        style_embedding = models.BinaryField(null=True, blank=True)  # Fallback for SQLite
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['style']),
        ]
    
    def __str__(self):
        return self.name


class Artwork(models.Model):
    """
    Artwork model with vector embeddings for visual similarity search
    Supports multi-modal content: images, 360° videos, audio narration
    """
    
    CATEGORY_CHOICES = [
        ('painting', 'Painting'),
        ('sculpture', 'Sculpture'),
        ('photography', 'Photography'),
        ('installation', 'Installation'),
        ('digital', 'Digital Art'),
        ('mixed', 'Mixed Media'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    museum = models.ForeignKey(Museum, on_delete=models.CASCADE, related_name='artworks')
    artist = models.ForeignKey(Artist, on_delete=models.SET_NULL, null=True, related_name='artworks')
    
    # Basic Information
    title = models.CharField(max_length=255)
    description = models.TextField()
    year_created = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    medium = models.CharField(max_length=255, blank=True)
    dimensions = models.CharField(max_length=100, blank=True)
    
    # Location
    gallery_location = models.CharField(max_length=255, blank=True)
    room_number = models.CharField(max_length=50, blank=True)
    
    # GPS Coordinates (captured during artifact upload)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    geofence_radius_meters = models.IntegerField(default=100, help_text="Radius in meters for geofencing")
    
    # Media Files
    image = models.ImageField(
        upload_to='artworks/images/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    video_360 = models.FileField(
        upload_to='artworks/videos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['mp4', 'webm'])]
    )
    audio_narration = models.FileField(
        upload_to='artworks/audio/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['mp3', 'wav', 'ogg'])]
    )
    
    # Vector Embedding (512-dimensional CLIP embedding - PostgreSQL only)
    if VECTOR_AVAILABLE:
        embedding = VectorField(dimensions=512, null=True, blank=True)
    else:
        embedding = models.BinaryField(null=True, blank=True)  # Fallback for SQLite
        
    embedding_model = models.CharField(max_length=50, default='clip-ViT-B-32')
    embedding_generated_at = models.DateTimeField(null=True, blank=True)
    
    # Tags for hybrid search
    tags = models.JSONField(default=list, blank=True)
    historical_context = models.TextField(blank=True)
    
    # Metadata
    provenance = models.TextField(blank=True)
    acquisition_date = models.DateField(null=True, blank=True)
    
    # Analytics counters (denormalized for performance)
    view_count = models.IntegerField(default=0)
    scan_count = models.IntegerField(default=0)
    avg_dwell_time_seconds = models.FloatField(default=0.0)
    
    # Status
    is_on_display = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['museum', 'is_on_display']),
            models.Index(fields=['artist']),
            models.Index(fields=['category']),
            models.Index(fields=['title']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.artist.name if self.artist else 'Unknown'}"


class ArtworkTranslation(models.Model):
    """
    Multi-language support for artwork descriptions
    Allows museums to provide descriptions in multiple languages
    """
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('zh', 'Chinese'),
        ('ja', 'Japanese'),
        ('ar', 'Arabic'),
        ('hi', 'Hindi'),
        ('pt', 'Portuguese'),
        ('kn', 'Kannada'),  # Indian language
        ('ta', 'Tamil'),    # Indian language
        ('te', 'Telugu'),   # Indian language
        ('ml', 'Malayalam'), # Indian language
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    historical_context = models.TextField(blank=True)
    
    # Audio narration for this language
    audio_narration = models.FileField(
        upload_to='artworks/audio/translations/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['mp3', 'wav', 'ogg'])]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['artwork', 'language']
        ordering = ['language']
    
    def __str__(self):
        return f"{self.artwork.title} ({self.get_language_display()})"


class VisitorSession(models.Model):
    """
    Anonymous visitor session tracking (privacy-first)
    No personal identifiers stored - only session UUID
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    museum = models.ForeignKey(Museum, on_delete=models.CASCADE, related_name='sessions')
    
    # Session metadata (no PII)
    session_start = models.DateTimeField(auto_now_add=True)
    session_end = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    
    # Device info (anonymized)
    device_type = models.CharField(max_length=50, blank=True)  # mobile/tablet/desktop
    browser = models.CharField(max_length=50, blank=True)
    
    # Privacy flags
    analytics_consent = models.BooleanField(default=True)
    opted_out = models.BooleanField(default=False)
    
    # Session summary
    artworks_scanned = models.IntegerField(default=0)
    total_interactions = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-session_start']
        indexes = [
            models.Index(fields=['museum', 'session_start']),
            models.Index(fields=['session_start']),
        ]
    
    def __str__(self):
        return f"Session {self.id} - {self.museum.name}"


class ArtworkInteraction(models.Model):
    """
    Individual artwork interactions within a visitor session
    """
    
    INTERACTION_TYPES = [
        ('scan', 'Artwork Scan'),
        ('view_details', 'View Details'),
        ('play_audio', 'Play Audio Narration'),
        ('watch_video', 'Watch 360° Video'),
        ('view_related', 'View Related Artworks'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='interactions')
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='interactions')
    
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    dwell_time_seconds = models.IntegerField(default=0)
    
    # Similarity score (for scan interactions)
    similarity_score = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['artwork', 'interaction_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.interaction_type} - {self.artwork.title}"


class VisitorFeedback(models.Model):
    """
    Optional visitor feedback (anonymous)
    """
    
    REACTION_CHOICES = [
        ('love', '❤️ Love it'),
        ('like', '👍 Like it'),
        ('neutral', '😐 Neutral'),
        ('dislike', '👎 Dislike'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='feedback')
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='feedback')
    
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    comment = models.TextField(blank=True, max_length=500)
    sentiment_score = models.FloatField(null=True, blank=True)  # -1 to 1
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['artwork', 'reaction']),
        ]
    
    def __str__(self):
        return f"{self.reaction} - {self.artwork.title}"


class CachedEmbedding(models.Model):
    """
    Cache frequently accessed embeddings for performance (PostgreSQL only)
    """
    
    artwork = models.OneToOneField(Artwork, on_delete=models.CASCADE, related_name='cached_embedding')
    
    if VECTOR_AVAILABLE:
        embedding = VectorField(dimensions=512)
    else:
        embedding = models.BinaryField(null=True, blank=True)  # Fallback for SQLite
        
    access_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-access_count']
        indexes = [
            models.Index(fields=['access_count']),
        ]
    
    def __str__(self):
        return f"Cached: {self.artwork.title}"


class SystemLog(models.Model):
    """
    Audit logging for privacy compliance and debugging
    """
    
    LOG_TYPES = [
        ('embedding_generation', 'Embedding Generation'),
        ('data_access', 'Data Access'),
        ('analytics_export', 'Analytics Export'),
        ('privacy_opt_out', 'Privacy Opt-Out'),
        ('error', 'System Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    log_type = models.CharField(max_length=30, choices=LOG_TYPES)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['log_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.log_type} - {self.created_at}"


class NavigationWaypoint(models.Model):
    """
    Waypoints for indoor museum navigation with 360° video capture
    Staff walks through museum recording path, visitors use it for navigation
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    museum = models.ForeignKey(Museum, on_delete=models.CASCADE, related_name='waypoints')
    artwork = models.ForeignKey(
        Artwork, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='waypoints',
        help_text="Artwork located at this waypoint (if any)"
    )
    
    # Location Data
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    floor_level = models.IntegerField(default=1, help_text="Floor number (1=Ground, 2=First, etc.)")
    room_name = models.CharField(max_length=100, blank=True, help_text="E.g., 'Renaissance Gallery'")
    
    # Visual Reference for Position Matching
    video_360 = models.FileField(
        upload_to='navigation/waypoints/',
        validators=[FileExtensionValidator(['mp4', 'webm'])],
        help_text="360° video captured at this location for visual matching"
    )
    thumbnail = models.ImageField(
        upload_to='navigation/thumbnails/',
        blank=True,
        null=True,
        help_text="Preview image extracted from 360° video"
    )
    
    # Navigation Instructions
    title = models.CharField(max_length=255, help_text="E.g., 'Entrance Hall', 'Gallery Intersection'")
    description = models.TextField(blank=True, help_text="Landmarks or directions visible from here")
    voice_instruction = models.TextField(blank=True, help_text="Text for TTS: 'Walk 20 steps forward...'")
    
    # Path Connections
    sequence_order = models.IntegerField(default=0, help_text="Order in the navigation path")
    next_waypoint = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_waypoint',
        help_text="Next step in the navigation sequence"
    )
    
    # Distance & Timing
    distance_to_next_meters = models.FloatField(
        null=True, 
        blank=True,
        help_text="Distance to next waypoint in meters"
    )
    estimated_walk_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Estimated time to walk to next waypoint"
    )
    
    # Visual Embedding for Position Matching (frame from 360° video)
    if VECTOR_AVAILABLE:
        position_embedding = VectorField(dimensions=512, null=True, blank=True)
    else:
        position_embedding = models.BinaryField(null=True, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        MuseumStaff,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_waypoints'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['museum', 'floor_level', 'sequence_order']
        indexes = [
            models.Index(fields=['museum', 'floor_level', 'is_active']),
            models.Index(fields=['sequence_order']),
            models.Index(fields=['artwork']),
        ]
    
    def __str__(self):
        artwork_info = f" -> {self.artwork.title}" if self.artwork else ""
        return f"{self.museum.name} - {self.title}{artwork_info}"


class NavigationPath(models.Model):
    """
    Pre-defined navigation routes through the museum
    E.g., 'Renaissance Tour', 'Modern Art Collection', 'Quick Tour'
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    museum = models.ForeignKey(Museum, on_delete=models.CASCADE, related_name='navigation_paths')
    
    # Path Information
    name = models.CharField(max_length=255, help_text="E.g., 'Highlights Tour', 'Complete Exhibition'")
    description = models.TextField()
    duration_minutes = models.IntegerField(help_text="Estimated tour duration")
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy - Wheelchair Accessible'),
            ('moderate', 'Moderate - Some stairs'),
            ('challenging', 'Challenging - Multiple floors')
        ],
        default='easy'
    )
    
    # Waypoints in this path (stored as ordered list of IDs)
    waypoint_sequence = models.JSONField(
        default=list,
        help_text="Ordered list of waypoint UUIDs"
    )
    
    # Path Metadata
    total_distance_meters = models.FloatField(default=0)
    artwork_count = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Analytics
    usage_count = models.IntegerField(default=0)
    avg_completion_rate = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-usage_count']
        indexes = [
            models.Index(fields=['museum', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.museum.name} - {self.name}"


class VisitorNavigation(models.Model):
    """
    Track visitor navigation sessions for analytics and assistance
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        VisitorSession,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='navigation_sessions'
    )
    path = models.ForeignKey(
        NavigationPath,
        on_delete=models.SET_NULL,
        null=True,
        related_name='visitor_sessions'
    )
    
    # Current Status
    current_waypoint = models.ForeignKey(
        NavigationWaypoint,
        on_delete=models.SET_NULL,
        null=True,
        related_name='current_visitors'
    )
    target_artwork = models.ForeignKey(
        Artwork,
        on_delete=models.SET_NULL,
        null=True,
        related_name='navigation_targets'
    )
    
    # Progress Tracking
    visited_waypoints = models.JSONField(
        default=list,
        help_text="List of visited waypoint UUIDs with timestamps"
    )
    completion_percentage = models.FloatField(default=0.0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('abandoned', 'Abandoned'),
        ],
        default='active'
    )
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['session', 'status']),
        ]
    
    def __str__(self):
        return f"Navigation {self.id} - {self.status}"
