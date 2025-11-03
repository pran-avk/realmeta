"""
Django Signals for Automatic Translation
Note: Embedding generation disabled (requires Redis/Celery)
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Artwork, CachedEmbedding, SystemLog
from core.translation_utils import auto_translate_artwork


# Embedding generation disabled - requires Redis/Celery which isn't available on free tier
# @receiver(post_save, sender=Artwork)
# def auto_generate_embedding(sender, instance, created, **kwargs):
#     """
#     Automatically generate embedding when artwork is created or image is updated
#     Runs asynchronously via Celery
#     """
#     if created or not instance.embedding:
#         # Trigger async task to generate embedding
#         generate_artwork_embedding.delay(str(instance.id))
#         
#         # Log the action
#         SystemLog.objects.create(
#             log_type='embedding_generation',
#             message=f'Embedding generation queued for artwork: {instance.title}',
#             metadata={
#                 'artwork_id': str(instance.id),
#                 'artwork_title': instance.title,
#                 'museum': instance.museum.name
#             }
#         )


@receiver(post_save, sender=Artwork)
def auto_translate_description(sender, instance, created, **kwargs):
    """
    Automatically translate artwork description to all supported languages
    Runs when artwork is created or description is updated
    """
    if created:
        try:
            # Auto-translate to all languages
            auto_translate_artwork(instance)
            
            # Log the action
            SystemLog.objects.create(
                log_type='translation',
                message=f'Auto-translation completed for artwork: {instance.title}',
                metadata={
                    'artwork_id': str(instance.id),
                    'artwork_title': instance.title,
                    'languages': 13  # Total supported languages
                }
            )
        except Exception as e:
            SystemLog.objects.create(
                log_type='error',
                message=f'Auto-translation failed: {str(e)}',
                metadata={
                    'artwork_id': str(instance.id),
                    'error': str(e)
                }
            )


@receiver(post_delete, sender=Artwork)
def cleanup_cached_embedding(sender, instance, **kwargs):
    """
    Clean up cached embeddings when artwork is deleted
    """
    CachedEmbedding.objects.filter(artwork=instance).delete()
