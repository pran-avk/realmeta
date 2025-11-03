"""
Background Tasks for Asynchronous Processing
NOTE: Celery is DISABLED for free tier deployment (no Redis available)
These functions are kept for future use when Redis/Celery becomes available.
"""
# Celery disabled - importing would fail without celery package
# from celery import shared_task
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger('artscope')


# @shared_task(bind=True, max_retries=3)
def generate_artwork_embedding(artwork_id: str):
    """
    Generate embedding for an artwork
    NOTE: Embedding generation DISABLED (requires PyTorch/CLIP and Celery)
    
    Args:
        artwork_id: UUID of the artwork
    """
    try:
        from core.models import Artwork, SystemLog
        
        artwork = Artwork.objects.get(id=artwork_id)
        
        logger.info(f"Embedding generation skipped for artwork: {artwork.title} (feature disabled)")
        
        # Log that embedding is disabled
        SystemLog.objects.create(
            log_type='embedding_generation',
            message=f'Embedding generation skipped for artwork: {artwork.title} (feature disabled)',
            metadata={
                'artwork_id': str(artwork.id),
                'artwork_title': artwork.title,
                'status': 'disabled'
            }
        )
        
        return f"Embedding generation disabled for {artwork.title}"
        
    except Exception as e:
        logger.error(f"Error in embedding function for artwork {artwork_id}: {e}")
        raise


# @shared_task
def batch_generate_embeddings(artwork_ids: list):
    """
    Batch generate embeddings for multiple artworks
    NOTE: DISABLED - requires Celery
    
    Args:
        artwork_ids: List of artwork UUIDs
    """
    logger.info(f"Batch embedding generation disabled for {len(artwork_ids)} artworks")
    return f"Embedding generation disabled"


# @shared_task
def cleanup_old_sessions():
    """
    Clean up old visitor sessions based on data retention policy
    NOTE: DISABLED - requires Celery scheduled tasks
    """
    try:
        from core.models import Museum, VisitorSession
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=90)
        
        for museum in Museum.objects.filter(analytics_enabled=True):
            retention_days = museum.data_retention_days
            museum_cutoff = timezone.now() - timedelta(days=retention_days)
            
            deleted_count = VisitorSession.objects.filter(
                museum=museum,
                session_start__lt=museum_cutoff
            ).delete()[0]
            
            logger.info(f"Cleaned up {deleted_count} sessions for {museum.name}")
        
        return "Session cleanup completed"
        
    except Exception as e:
        logger.error(f"Error during session cleanup: {e}")
        raise


# @shared_task
def aggregate_analytics():
    """
    Aggregate analytics data for dashboard (runs daily)
    NOTE: DISABLED - requires Celery scheduled tasks
    """
    try:
        from analytics.utils import calculate_museum_analytics
        from core.models import Museum
        
        for museum in Museum.objects.filter(analytics_enabled=True):
            calculate_museum_analytics(museum.id)
        
        return "Analytics aggregation completed"
        
    except Exception as e:
        logger.error(f"Error during analytics aggregation: {e}")
        raise


# @shared_task
def update_artwork_counters():
    """
    Update denormalized counters on Artwork model
    NOTE: DISABLED - requires Celery scheduled tasks
    """
    try:
        from core.models import Artwork, ArtworkInteraction
        from django.db.models import Count, Avg
        
        artworks = Artwork.objects.all()
        
        for artwork in artworks:
            interactions = ArtworkInteraction.objects.filter(artwork=artwork)
            
            artwork.scan_count = interactions.filter(interaction_type='scan').count()
            artwork.view_count = interactions.count()
            artwork.avg_dwell_time_seconds = interactions.aggregate(
                Avg('dwell_time_seconds')
            )['dwell_time_seconds__avg'] or 0.0
            
            artwork.save(update_fields=['scan_count', 'view_count', 'avg_dwell_time_seconds'])
        
        logger.info(f"Updated counters for {artworks.count()} artworks")
        return "Artwork counters updated"
        
    except Exception as e:
        logger.error(f"Error updating artwork counters: {e}")
        raise


# @shared_task
def process_visitor_feedback():
    """
    Process visitor feedback and calculate sentiment scores
    NOTE: DISABLED - requires Celery scheduled tasks
    """
    try:
        from core.models import VisitorFeedback
        # TextBlob not installed - sentiment analysis disabled
        # from textblob import TextBlob
        
        feedback_items = VisitorFeedback.objects.filter(sentiment_score__isnull=True)
        
        logger.info(f"Sentiment analysis disabled for {feedback_items.count()} feedback items")
        return "Feedback processing disabled"
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise
