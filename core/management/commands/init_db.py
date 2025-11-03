"""
Database initialization script
Sets up pgvector extension for Neon PostgreSQL
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Initialize database with pgvector extension'
    
    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Enable pgvector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            self.stdout.write(self.style.SUCCESS('✓ pgvector extension enabled'))
            
            # Create indexes for vector similarity search
            self.stdout.write('Creating vector indexes...')
            
            # Index for artwork embeddings
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS artwork_embedding_idx 
                    ON core_artwork 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)
                self.stdout.write(self.style.SUCCESS('✓ Artwork embedding index created'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Index may already exist: {e}'))
            
            # Index for cached embeddings
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS cached_embedding_idx 
                    ON core_cachedembedding 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 50);
                """)
                self.stdout.write(self.style.SUCCESS('✓ Cached embedding index created'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Index may already exist: {e}'))
            
        self.stdout.write(self.style.SUCCESS('\n✅ Database initialization complete!'))
