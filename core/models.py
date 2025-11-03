"""
Core Models for ArtScope
Advanced database models with vector embeddings, analytics, and privacy features
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from pgvector.django import VectorField
import uuid


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
    
    # Style embedding for artist-based recommendations
    style_embedding = VectorField(dimensions=512, null=True, blank=True)
    
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
    
    # Vector Embedding (512-dimensional CLIP embedding)
    embedding = VectorField(dimensions=512, null=True, blank=True)
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
    Cache frequently accessed embeddings for performance
    """
    
    artwork = models.OneToOneField(Artwork, on_delete=models.CASCADE, related_name='cached_embedding')
    embedding = VectorField(dimensions=512)
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
