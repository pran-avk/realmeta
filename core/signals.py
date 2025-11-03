"""
Django Signals for Automatic Translation and Embedding Generation
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Artwork, CachedEmbedding, SystemLog
from core.translation_utils import auto_translate_artwork
import logging

logger = logging.getLogger('artscope')


@receiver(post_save, sender=Artwork)
def auto_generate_embedding(sender, instance, created, **kwargs):
    """
    Automatically generate MobileNetV2 embedding when artwork is created or image updated
    Runs synchronously (no Celery needed)
    """
    if created or not instance.embedding:
        try:
            from embeddings.mobilenet_engine import mobilenet_engine
            
            # Generate embedding from artwork image
            if instance.image:
                logger.info(f"Generating embedding for: {instance.title}")
                
                embedding = mobilenet_engine.generate_embedding(instance.image.path)
                
                # Save embedding to database
                instance.embedding = embedding.tolist()
                instance.save(update_fields=['embedding'])
                
                logger.info(f"✅ Embedding generated for: {instance.title}")
                
                # Log success
                SystemLog.objects.create(
                    log_type='embedding_generation',
                    message=f'MobileNetV2 embedding generated for: {instance.title}',
                    metadata={
                        'artwork_id': str(instance.id),
                        'artwork_title': instance.title,
                        'embedding_size': len(embedding)
                    }
                )
        except Exception as e:
            logger.error(f"Embedding generation failed for {instance.id}: {str(e)}")
            try:
                SystemLog.objects.create(
                    log_type='error',
                    message=f'Embedding generation failed: {str(e)}',
                    metadata={
                        'artwork_id': str(instance.id),
                        'error': str(e)
                    }
                )
            except:
                pass


@receiver(post_save, sender=Artwork)
def auto_translate_description(sender, instance, created, **kwargs):
    """
    Automatically translate artwork description to all supported languages
    Runs when artwork is created or description is updated
    NOTE: Runs synchronously - errors are logged but don't block artwork creation
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
            # Log error but don't raise - artwork should still be created
            import logging
            logger = logging.getLogger('artscope')
            logger.error(f'Auto-translation failed for artwork {instance.id}: {str(e)}')
            
            try:
                SystemLog.objects.create(
                    log_type='error',
                    message=f'Auto-translation failed: {str(e)}',
                    metadata={
                        'artwork_id': str(instance.id),
                        'error': str(e)
                    }
                )
            except:
                pass  # Don't let logging failure break anything


@receiver(post_delete, sender=Artwork)
def cleanup_cached_embedding(sender, instance, **kwargs):
    """
    Clean up cached embeddings when artwork is deleted
    """
    CachedEmbedding.objects.filter(artwork=instance).delete()
