"""
Django Signals for Automatic Embedding Generation
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Artwork, CachedEmbedding, SystemLog
from embeddings.tasks import generate_artwork_embedding


@receiver(post_save, sender=Artwork)
def auto_generate_embedding(sender, instance, created, **kwargs):
    """
    Automatically generate embedding when artwork is created or image is updated
    Runs asynchronously via Celery
    """
    if created or not instance.embedding:
        # Trigger async task to generate embedding
        generate_artwork_embedding.delay(str(instance.id))
        
        # Log the action
        SystemLog.objects.create(
            log_type='embedding_generation',
            message=f'Embedding generation queued for artwork: {instance.title}',
            metadata={
                'artwork_id': str(instance.id),
                'artwork_title': instance.title,
                'museum': instance.museum.name
            }
        )


@receiver(post_delete, sender=Artwork)
def cleanup_cached_embedding(sender, instance, **kwargs):
    """
    Clean up cached embeddings when artwork is deleted
    """
    CachedEmbedding.objects.filter(artwork=instance).delete()
