"""
Celery Tasks for Asynchronous Processing
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger('artscope')


@shared_task(bind=True, max_retries=3)
def generate_artwork_embedding(self, artwork_id: str):
    """
    Generate embedding for an artwork asynchronously
    
    Args:
        artwork_id: UUID of the artwork
    """
    try:
        from core.models import Artwork, SystemLog
        from embeddings.engine import embedding_engine
        
        artwork = Artwork.objects.get(id=artwork_id)
        
        # Generate embedding
        embedding = embedding_engine.generate_embedding(artwork.image.path)
        
        # Save to database
        artwork.embedding = embedding.tolist()
        artwork.embedding_generated_at = timezone.now()
        artwork.save(update_fields=['embedding', 'embedding_generated_at'])
        
        logger.info(f"Embedding generated for artwork: {artwork.title}")
        
        # Log success
        SystemLog.objects.create(
            log_type='embedding_generation',
            message=f'Embedding generated successfully for artwork: {artwork.title}',
            metadata={
                'artwork_id': str(artwork.id),
                'artwork_title': artwork.title,
                'task_id': self.request.id
            }
        )
        
        return f"Embedding generated for {artwork.title}"
        
    except Exception as e:
        logger.error(f"Error generating embedding for artwork {artwork_id}: {e}")
        
        # Retry logic
        try:
            self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        except Exception as retry_exc:
            logger.error(f"Max retries reached for artwork {artwork_id}: {retry_exc}")
            
            # Log failure
            SystemLog.objects.create(
                log_type='error',
                message=f'Failed to generate embedding after retries',
                metadata={
                    'artwork_id': str(artwork_id),
                    'error': str(e),
                    'retries': self.request.retries
                }
            )
        raise


@shared_task
def batch_generate_embeddings(artwork_ids: list):
    """
    Batch generate embeddings for multiple artworks
    
    Args:
        artwork_ids: List of artwork UUIDs
    """
    for artwork_id in artwork_ids:
        generate_artwork_embedding.delay(artwork_id)
    
    return f"Queued {len(artwork_ids)} embeddings for generation"


@shared_task
def cleanup_old_sessions():
    """
    Clean up old visitor sessions based on data retention policy
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


@shared_task
def aggregate_analytics():
    """
    Aggregate analytics data for dashboard (runs daily)
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


@shared_task
def update_artwork_counters():
    """
    Update denormalized counters on Artwork model
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


@shared_task
def process_visitor_feedback():
    """
    Process visitor feedback and calculate sentiment scores
    """
    try:
        from core.models import VisitorFeedback
        from textblob import TextBlob
        
        feedback_items = VisitorFeedback.objects.filter(sentiment_score__isnull=True)
        
        for feedback in feedback_items:
            if feedback.comment:
                # Analyze sentiment
                blob = TextBlob(feedback.comment)
                feedback.sentiment_score = blob.sentiment.polarity
                feedback.save(update_fields=['sentiment_score'])
        
        logger.info(f"Processed sentiment for {feedback_items.count()} feedback items")
        return "Feedback processing completed"
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise
