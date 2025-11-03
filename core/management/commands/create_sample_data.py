"""
Sample data creation script for testing
"""
from django.core.management.base import BaseCommand
from django.core.files import File
from core.models import Museum, Artist, Artwork
from django.contrib.auth import get_user_model
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample museum
        museum, created = Museum.objects.get_or_create(
            name='The Metropolitan Museum of Art',
            defaults={
                'description': 'One of the world\'s largest and finest art museums',
                'location': 'New York, NY',
                'contact_email': 'info@metmuseum.org',
                'website': 'https://www.metmuseum.org',
                'analytics_enabled': True,
                'allow_visitor_feedback': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created museum: {museum.name}'))
        
        # Create sample artists
        artists_data = [
            {
                'name': 'Vincent van Gogh',
                'birth_year': 1853,
                'death_year': 1890,
                'nationality': 'Dutch',
                'style': 'Post-Impressionism',
                'biography': 'Dutch post-impressionist painter who is among the most famous and influential figures in the history of Western art.'
            },
            {
                'name': 'Leonardo da Vinci',
                'birth_year': 1452,
                'death_year': 1519,
                'nationality': 'Italian',
                'style': 'Renaissance',
                'biography': 'Italian polymath of the Renaissance whose areas of interest included invention, painting, sculpting, and science.'
            },
            {
                'name': 'Pablo Picasso',
                'birth_year': 1881,
                'death_year': 1973,
                'nationality': 'Spanish',
                'style': 'Cubism',
                'biography': 'Spanish painter, sculptor, printmaker, ceramicist and theatre designer who spent most of his adult life in France.'
            }
        ]
        
        artists = []
        for artist_data in artists_data:
            artist, created = Artist.objects.get_or_create(
                name=artist_data['name'],
                defaults=artist_data
            )
            artists.append(artist)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created artist: {artist.name}'))
        
        # Create sample artworks
        artworks_data = [
            {
                'title': 'Starry Night',
                'artist': artists[0],
                'description': 'A famous painting depicting the view from van Gogh\'s asylum room window at night.',
                'year_created': 1889,
                'category': 'painting',
                'medium': 'Oil on canvas',
                'tags': ['night', 'stars', 'landscape', 'post-impressionism']
            },
            {
                'title': 'Mona Lisa',
                'artist': artists[1],
                'description': 'A half-length portrait painting by Leonardo da Vinci.',
                'year_created': 1503,
                'category': 'painting',
                'medium': 'Oil on poplar panel',
                'tags': ['portrait', 'renaissance', 'mysterious smile']
            },
            {
                'title': 'Guernica',
                'artist': artists[2],
                'description': 'A powerful anti-war painting created in response to the bombing of Guernica.',
                'year_created': 1937,
                'category': 'painting',
                'medium': 'Oil on canvas',
                'tags': ['war', 'cubism', 'political', 'monochrome']
            }
        ]
        
        for artwork_data in artworks_data:
            artwork, created = Artwork.objects.get_or_create(
                title=artwork_data['title'],
                museum=museum,
                defaults={
                    **artwork_data,
                    'gallery_location': 'Main Gallery',
                    'is_on_display': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created artwork: {artwork.title}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Sample data creation complete!'))
        self.stdout.write(self.style.WARNING('\nNote: Add actual artwork images to enable embedding generation'))
