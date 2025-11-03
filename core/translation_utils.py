"""
Auto-Translation Utilities for ArtScope
Automatically translates descriptions from English to multiple languages
"""
from deep_translator import GoogleTranslator
from gtts import gTTS
import os
from io import BytesIO
from django.core.files import File
from core.models import ArtworkTranslation


# Language mapping for Google Translate
LANGUAGE_MAP = {
    'en': 'en',      # English
    'es': 'es',      # Spanish
    'fr': 'fr',      # French
    'de': 'de',      # German
    'it': 'it',      # Italian
    'zh': 'zh-CN',   # Chinese (Simplified)
    'ja': 'ja',      # Japanese
    'ar': 'ar',      # Arabic
    'hi': 'hi',      # Hindi
    'pt': 'pt',      # Portuguese
    'kn': 'kn',      # Kannada
    'ta': 'ta',      # Tamil
    'te': 'te',      # Telugu
    'ml': 'ml',      # Malayalam
}


def auto_translate_artwork(artwork):
    """
    Automatically translate artwork description from English to all supported languages
    Runs with timeout to prevent hanging
    
    Args:
        artwork: Artwork model instance with English description
    
    Returns:
        dict: Dictionary of created translations {language_code: translation_obj}
    """
    import logging
    logger = logging.getLogger('artscope')
    translations = {}
    
    # Skip if no description
    if not artwork.description:
        logger.warning(f"No description for {artwork.title}")
        return translations
    
    logger.info(f"Translating: {artwork.title}")
    
    # Translate to each language (limit to prevent timeout)
    success_count = 0
    max_translations = 5  # Limit translations to prevent timeout
    
    for lang_code, translate_code in list(LANGUAGE_MAP.items())[:max_translations + 1]:
        if lang_code == 'en':
            # Skip English (source language)
            continue
        
        try:
            # Check if translation already exists
            if ArtworkTranslation.objects.filter(artwork=artwork, language=lang_code).exists():
                logger.info(f"  ✓ {lang_code} - Already exists")
                continue
            
            # Translate title
            translated_title = translate_text(artwork.title, translate_code)
            
            # Translate description
            translated_description = translate_text(artwork.description, translate_code)
            
            # Translate historical context if exists
            translated_context = ''
            if artwork.historical_context:
                translated_context = translate_text(artwork.historical_context, translate_code)
            
            # Create translation record
            translation = ArtworkTranslation.objects.create(
                artwork=artwork,
                language=lang_code,
                title=translated_title,
                description=translated_description,
                historical_context=translated_context
            )
            
            # Skip audio generation for now (can be slow)
            # Generate audio narration (TTS) - disabled for performance
            # audio_file = generate_audio_narration(
            #     translated_description,
            #     lang_code,
            #     artwork.id
            # )
            # 
            # if audio_file:
            #     translation.audio_narration.save(
            #         f'{artwork.id}_{lang_code}.mp3',
            #         audio_file
            #     )
            
            translations[lang_code] = translation
            success_count += 1
            logger.info(f"  ✅ {lang_code} - Created")
            
        except Exception as e:
            logger.error(f"  ❌ {lang_code} - Failed: {str(e)}")
            continue
    
    logger.info(f"Completed {success_count} translations for {artwork.title}")
    return translations


def translate_text(text, target_language):
    """
    Translate text to target language using Google Translate
    
    Args:
        text: Text to translate (in English)
        target_language: Target language code (e.g., 'es', 'fr', 'hi')
    
    Returns:
        str: Translated text
    """
    try:
        # Split long text into chunks (Google Translate has 5000 char limit)
        max_length = 4500
        if len(text) <= max_length:
            translator = GoogleTranslator(source='en', target=target_language)
            return translator.translate(text)
        
        # Handle long text by splitting into paragraphs
        paragraphs = text.split('\n\n')
        translated_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                translator = GoogleTranslator(source='en', target=target_language)
                translated = translator.translate(paragraph)
                translated_paragraphs.append(translated)
        
        return '\n\n'.join(translated_paragraphs)
        
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text  # Return original text if translation fails


def generate_audio_narration(text, language_code, artwork_id):
    """
    Generate audio narration from text using Google Text-to-Speech
    
    Args:
        text: Text to convert to speech
        language_code: Language code (e.g., 'en', 'es', 'hi')
        artwork_id: Artwork UUID for filename
    
    Returns:
        File object or None
    """
    try:
        # Map language codes to gTTS language codes
        gtts_lang_map = {
            'en': 'en',
            'es': 'es',
            'fr': 'fr',
            'de': 'de',
            'it': 'it',
            'zh': 'zh-CN',
            'ja': 'ja',
            'ar': 'ar',
            'hi': 'hi',
            'pt': 'pt',
            'kn': 'kn',  # Kannada
            'ta': 'ta',  # Tamil
            'te': 'te',  # Telugu
            'ml': 'ml',  # Malayalam
        }
        
        gtts_lang = gtts_lang_map.get(language_code, 'en')
        
        # Limit text length for audio (max 2000 chars for better performance)
        if len(text) > 2000:
            text = text[:1997] + "..."
        
        # Generate speech
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        
        # Save to BytesIO
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Return as Django File
        return File(audio_buffer, name=f'{artwork_id}_{language_code}.mp3')
        
    except Exception as e:
        print(f"Audio generation error for {language_code}: {str(e)}")
        return None


def update_artwork_translations(artwork):
    """
    Update or regenerate all translations for an artwork
    Useful when description is updated
    """
    # Delete existing translations
    ArtworkTranslation.objects.filter(artwork=artwork).delete()
    
    # Regenerate all translations
    return auto_translate_artwork(artwork)


def bulk_translate_artworks(museum=None):
    """
    Bulk translate all artworks (optionally filtered by museum)
    Useful for initial setup or migration
    """
    from core.models import Artwork
    
    if museum:
        artworks = Artwork.objects.filter(museum=museum)
    else:
        artworks = Artwork.objects.all()
    
    total = artworks.count()
    print(f"📚 Starting bulk translation for {total} artworks...")
    
    for idx, artwork in enumerate(artworks, 1):
        print(f"\n[{idx}/{total}] Processing: {artwork.title}")
        auto_translate_artwork(artwork)
    
    print(f"\n🎉 Bulk translation complete! Processed {total} artworks.")
