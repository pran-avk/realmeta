"""
Analytics Utilities
Calculate aggregated metrics and insights
"""
from django.db.models import Count, Avg, Sum, F
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import logging

logger = logging.getLogger('artscope')


def calculate_museum_analytics(museum_id: str, days: int = 30):
    """
    Calculate comprehensive analytics for a museum
    
    Args:
        museum_id: Museum UUID
        days: Number of days to analyze
        
    Returns:
        Dictionary with analytics data
    """
    from core.models import Museum, VisitorSession, ArtworkInteraction, Artwork
    
    try:
        museum = Museum.objects.get(id=museum_id)
        start_date = timezone.now() - timedelta(days=days)
        
        # Total sessions
        total_sessions = VisitorSession.objects.filter(
            museum=museum,
            session_start__gte=start_date,
            opted_out=False
        ).count()
        
        # Total interactions
        total_interactions = ArtworkInteraction.objects.filter(
            session__museum=museum,
            timestamp__gte=start_date
        ).count()
        
        # Average session duration
        avg_duration = VisitorSession.objects.filter(
            museum=museum,
            session_start__gte=start_date,
            opted_out=False
        ).aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
        
        # Most scanned artworks
        top_artworks = ArtworkInteraction.objects.filter(
            session__museum=museum,
            interaction_type='scan',
            timestamp__gte=start_date
        ).values('artwork__title', 'artwork__id').annotate(
            scan_count=Count('id')
        ).order_by('-scan_count')[:10]
        
        # Interaction type breakdown
        interaction_breakdown = ArtworkInteraction.objects.filter(
            session__museum=museum,
            timestamp__gte=start_date
        ).values('interaction_type').annotate(
            count=Count('id')
        )
        
        # Average dwell time per artwork
        avg_dwell_time = ArtworkInteraction.objects.filter(
            session__museum=museum,
            timestamp__gte=start_date
        ).aggregate(Avg('dwell_time_seconds'))['dwell_time_seconds__avg'] or 0
        
        # Daily visitor trends
        daily_trends = VisitorSession.objects.filter(
            museum=museum,
            session_start__gte=start_date,
            opted_out=False
        ).extra(
            select={'day': 'DATE(session_start)'}
        ).values('day').annotate(
            visitors=Count('id')
        ).order_by('day')
        
        analytics = {
            'museum_name': museum.name,
            'period_days': days,
            'total_sessions': total_sessions,
            'total_interactions': total_interactions,
            'avg_session_duration_minutes': round(avg_duration / 60, 2),
            'avg_dwell_time_seconds': round(avg_dwell_time, 2),
            'top_artworks': list(top_artworks),
            'interaction_breakdown': list(interaction_breakdown),
            'daily_trends': list(daily_trends),
        }
        
        # Cache results
        cache_key = f"analytics:museum:{museum_id}:{days}"
        cache.set(cache_key, analytics, 3600)  # Cache for 1 hour
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error calculating analytics for museum {museum_id}: {e}")
        raise


def get_artwork_insights(artwork_id: str):
    """
    Get detailed insights for a specific artwork
    
    Args:
        artwork_id: Artwork UUID
        
    Returns:
        Dictionary with artwork insights
    """
    from core.models import Artwork, ArtworkInteraction, VisitorFeedback
    
    try:
        artwork = Artwork.objects.get(id=artwork_id)
        
        # Total scans
        total_scans = artwork.interactions.filter(interaction_type='scan').count()
        
        # Average dwell time
        avg_dwell = artwork.interactions.aggregate(
            Avg('dwell_time_seconds')
        )['dwell_time_seconds__avg'] or 0
        
        # Interaction breakdown
        interaction_stats = artwork.interactions.values('interaction_type').annotate(
            count=Count('id')
        )
        
        # Feedback analysis
        feedback_stats = VisitorFeedback.objects.filter(artwork=artwork).values(
            'reaction'
        ).annotate(count=Count('id'))
        
        # Average sentiment
        avg_sentiment = VisitorFeedback.objects.filter(artwork=artwork).aggregate(
            Avg('sentiment_score')
        )['sentiment_score__avg']
        
        insights = {
            'artwork_title': artwork.title,
            'total_scans': total_scans,
            'avg_dwell_time_seconds': round(avg_dwell, 2),
            'interaction_stats': list(interaction_stats),
            'feedback_stats': list(feedback_stats),
            'avg_sentiment': round(avg_sentiment, 2) if avg_sentiment else None,
        }
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting insights for artwork {artwork_id}: {e}")
        raise


def generate_recommendation_score(visitor_session_id: str, artwork_id: str) -> float:
    """
    Generate personalized recommendation score for an artwork
    
    Args:
        visitor_session_id: Visitor session UUID
        artwork_id: Artwork UUID
        
    Returns:
        Recommendation score (0-1)
    """
    from core.models import VisitorSession, Artwork, ArtworkInteraction
    import numpy as np
    
    try:
        session = VisitorSession.objects.get(id=visitor_session_id)
        artwork = Artwork.objects.get(id=artwork_id)
        
        # Get previously viewed artworks in this session
        viewed_artworks = ArtworkInteraction.objects.filter(
            session=session
        ).values_list('artwork_id', flat=True)
        
        if not viewed_artworks:
            return 0.5  # Neutral score for first artwork
        
        # Get embeddings of viewed artworks
        viewed_embeddings = Artwork.objects.filter(
            id__in=viewed_artworks,
            embedding__isnull=False
        ).values_list('embedding', flat=True)
        
        if not viewed_embeddings or not artwork.embedding:
            return 0.5
        
        # Calculate average similarity to viewed artworks
        similarities = []
        for viewed_emb in viewed_embeddings:
            viewed_vec = np.array(viewed_emb)
            artwork_vec = np.array(artwork.embedding)
            similarity = np.dot(viewed_vec, artwork_vec) / (
                np.linalg.norm(viewed_vec) * np.linalg.norm(artwork_vec)
            )
            similarities.append(similarity)
        
        # Average similarity as recommendation score
        score = np.mean(similarities)
        return float(score)
        
    except Exception as e:
        logger.error(f"Error generating recommendation score: {e}")
        return 0.5


def get_heatmap_data(museum_id: str, days: int = 7):
    """
    Generate heatmap data for artwork interactions
    
    Args:
        museum_id: Museum UUID
        days: Number of days to analyze
        
    Returns:
        Heatmap data structure
    """
    from core.models import ArtworkInteraction
    from datetime import datetime
    
    try:
        start_date = timezone.now() - timedelta(days=days)
        
        # Get hourly interaction data
        interactions = ArtworkInteraction.objects.filter(
            session__museum_id=museum_id,
            timestamp__gte=start_date
        ).extra(
            select={
                'hour': 'EXTRACT(hour FROM timestamp)',
                'day_of_week': 'EXTRACT(dow FROM timestamp)'
            }
        ).values('hour', 'day_of_week').annotate(
            count=Count('id')
        )
        
        # Create heatmap matrix (7 days x 24 hours)
        heatmap = [[0 for _ in range(24)] for _ in range(7)]
        
        for item in interactions:
            day = int(item['day_of_week'])
            hour = int(item['hour'])
            heatmap[day][hour] = item['count']
        
        return {
            'data': heatmap,
            'days': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
            'hours': list(range(24))
        }
        
    except Exception as e:
        logger.error(f"Error generating heatmap data: {e}")
        raise
