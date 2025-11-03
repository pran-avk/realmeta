#!/bin/bash

# ArtScope Deployment Script for Render
# This script sets up the application on Render

echo "🎨 Starting ArtScope deployment..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Initialize database with pgvector
echo "🗄️ Initializing database..."
python manage.py init_db

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Create superuser if needed (optional)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "👤 Creating superuser..."
    python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || true
fi

echo "✅ ArtScope deployment complete!"
