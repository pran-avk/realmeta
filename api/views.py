"""
API Views for ArtScope
Advanced REST endpoints with AR scanning, analytics, and recommendations
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q, Prefetch
import numpy as np
import logging

from core.models import (
    Museum, Artist, Artwork, VisitorSession,
    ArtworkInteraction, VisitorFeedback
)
from .serializers import (
    MuseumSerializer, ArtistSerializer, ArtworkListSerializer,
    ArtworkDetailSerializer, ArtworkCreateSerializer, ScanRequestSerializer,
    ScanResultSerializer, VisitorSessionSerializer, ArtworkInteractionSerializer,
    VisitorFeedbackSerializer, AnalyticsSummarySerializer, RecommendationSerializer
)
from embeddings.engine import embedding_engine
from analytics.utils import (
    calculate_museum_analytics, get_artwork_insights,
    generate_recommendation_score, get_heatmap_data
)

logger = logging.getLogger('artscope')


class MuseumViewSet(viewsets.ModelViewSet):
    """
    Museum management endpoints
    """
    queryset = Museum.objects.filter(is_active=True)
    serializer_class = MuseumSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def analytics(self, request, pk=None):
        """Get analytics dashboard data for museum"""
        museum = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        # Check cache first
        cache_key = f"analytics:museum:{pk}:{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            serializer = AnalyticsSummarySerializer(cached_data)
            return Response(serializer.data)
        
        # Calculate analytics
        analytics_data = calculate_museum_analytics(str(pk), days)
        serializer = AnalyticsSummarySerializer(analytics_data)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def heatmap(self, request, pk=None):
        """Get heatmap data for visitor interactions"""
        museum = self.get_object()
        days = int(request.query_params.get('days', 7))
        
        heatmap_data = get_heatmap_data(str(pk), days)
        return Response(heatmap_data)


class ArtistViewSet(viewsets.ModelViewSet):
    """
    Artist management endpoints
    """
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ArtworkViewSet(viewsets.ModelViewSet):
    """
    Artwork management endpoints with vector search
    """
    queryset = Artwork.objects.select_related('artist', 'museum').filter(is_on_display=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArtworkListSerializer
        elif self.action == 'create' or self.action == 'update':
            return ArtworkCreateSerializer
        return ArtworkDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by museum
        museum_id = self.request.query_params.get('museum')
        if museum_id:
            queryset = queryset.filter(museum_id=museum_id)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by artist
        artist_id = self.request.query_params.get('artist')
        if artist_id:
            queryset = queryset.filter(artist_id=artist_id)
        
        # Search by title/description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(tags__contains=[search])
            )
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def insights(self, request, pk=None):
        """Get detailed insights for an artwork"""
        artwork = self.get_object()
        insights = get_artwork_insights(str(pk))
        return Response(insights)
    
    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """Find similar artworks using vector similarity"""
        artwork = self.get_object()
        
        if not artwork.embedding:
            return Response(
                {'error': 'Artwork embedding not available yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all artworks with embeddings
        artworks = Artwork.objects.filter(
            museum=artwork.museum,
            is_on_display=True,
            embedding__isnull=False
        ).exclude(id=artwork.id)
        
        # Calculate similarities
        similarities = []
        query_embedding = np.array(artwork.embedding)
        
        for other_artwork in artworks:
            other_embedding = np.array(other_artwork.embedding)
            similarity = embedding_engine.compute_similarity(
                query_embedding,
                other_embedding
            )
            similarities.append((other_artwork, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 5
        top_similar = [
            {
                'artwork': ArtworkListSerializer(art).data,
                'similarity_score': float(score)
            }
            for art, score in similarities[:5]
        ]
        
        return Response(top_similar)


@api_view(['POST'])
@permission_classes([AllowAny])
def scan_artwork(request):
    """
    Scan an artwork using image and return matched artwork with details
    This is the core AR recognition endpoint (no login required)
    """
    serializer = ScanRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        image = serializer.validated_data['image']
        museum_id = serializer.validated_data['museum_id']
        session_id = serializer.validated_data.get('session_id')
        
        # Get or create visitor session
        if session_id:
            try:
                visitor_session = VisitorSession.objects.get(id=session_id)
            except VisitorSession.DoesNotExist:
                visitor_session = VisitorSession.objects.create(
                    museum_id=museum_id,
                    analytics_consent=True
                )
        else:
            visitor_session = VisitorSession.objects.create(
                museum_id=museum_id,
                analytics_consent=True
            )
        
        # Save uploaded image temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            for chunk in image.chunks():
                tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        # Generate embedding for scanned image
        query_embedding = embedding_engine.generate_embedding(tmp_path)
        
        # Find similar artworks in the museum
        artworks = Artwork.objects.filter(
            museum_id=museum_id,
            is_on_display=True,
            embedding__isnull=False
        )
        
        # Calculate similarities
        matches = []
        for artwork in artworks:
            artwork_embedding = np.array(artwork.embedding)
            similarity = embedding_engine.compute_similarity(
                query_embedding,
                artwork_embedding
            )
            matches.append((artwork, similarity))
        
        # Sort by similarity
        matches.sort(key=lambda x: x[1], reverse=True)
        
        if not matches:
            return Response(
                {'error': 'No matching artwork found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get best match
        best_match_artwork, best_similarity = matches[0]
        
        # Check similarity threshold
        threshold = 0.75
        if best_similarity < threshold:
            return Response(
                {'error': 'No confident match found', 'best_score': float(best_similarity)},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Log the interaction
        ArtworkInteraction.objects.create(
            session=visitor_session,
            artwork=best_match_artwork,
            interaction_type='scan',
            similarity_score=float(best_similarity)
        )
        
        # Update session counters
        visitor_session.artworks_scanned += 1
        visitor_session.total_interactions += 1
        visitor_session.save()
        
        # Get recommendations
        recommendations = []
        if len(matches) > 1:
            for artwork, score in matches[1:6]:  # Top 5 recommendations
                recommendations.append(artwork)
        
        # Prepare response
        response_data = {
            'artwork': ArtworkDetailSerializer(best_match_artwork).data,
            'similarity_score': float(best_similarity),
            'session_id': str(visitor_session.id),
            'recommendations': ArtworkListSerializer(recommendations, many=True).data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error during artwork scan: {e}")
        return Response(
            {'error': 'An error occurred during scanning'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def log_interaction(request):
    """
    Log visitor interaction with artwork (anonymous)
    """
    serializer = ArtworkInteractionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    interaction = serializer.save()
    
    # Update session counter
    session = interaction.session
    session.total_interactions += 1
    session.save()
    
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_feedback(request):
    """
    Submit visitor feedback for artwork (anonymous)
    """
    serializer = VisitorFeedbackSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if museum allows feedback
    session_id = request.data.get('session')
    try:
        session = VisitorSession.objects.get(id=session_id)
        if not session.museum.allow_visitor_feedback:
            return Response(
                {'error': 'Feedback not enabled for this museum'},
                status=status.HTTP_403_FORBIDDEN
            )
    except VisitorSession.DoesNotExist:
        return Response(
            {'error': 'Invalid session'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    feedback = serializer.save()
    
    # Trigger sentiment analysis (async)
    from embeddings.tasks import process_visitor_feedback
    process_visitor_feedback.delay()
    
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_recommendations(request):
    """
    Get personalized artwork recommendations based on session history
    """
    session_id = request.query_params.get('session_id')
    museum_id = request.query_params.get('museum_id')
    
    if not session_id or not museum_id:
        return Response(
            {'error': 'session_id and museum_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        session = VisitorSession.objects.get(id=session_id)
        
        # Get viewed artworks
        viewed_artwork_ids = ArtworkInteraction.objects.filter(
            session=session
        ).values_list('artwork_id', flat=True)
        
        # Get candidate artworks (not yet viewed)
        candidate_artworks = Artwork.objects.filter(
            museum_id=museum_id,
            is_on_display=True,
            embedding__isnull=False
        ).exclude(id__in=viewed_artwork_ids)
        
        # Calculate recommendation scores
        recommendations = []
        for artwork in candidate_artworks:
            score = generate_recommendation_score(session_id, str(artwork.id))
            recommendations.append({
                'artwork': ArtworkListSerializer(artwork).data,
                'score': score,
                'reason': 'Based on your viewing history'
            })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top 10
        serializer = RecommendationSerializer(recommendations[:10], many=True)
        return Response(serializer.data)
        
    except VisitorSession.DoesNotExist:
        return Response(
            {'error': 'Invalid session'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def opt_out_analytics(request):
    """
    Allow visitors to opt out of analytics tracking
    """
    session_id = request.data.get('session_id')
    
    if not session_id:
        return Response(
            {'error': 'session_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        session = VisitorSession.objects.get(id=session_id)
        session.opted_out = True
        session.analytics_consent = False
        session.save()
        
        return Response({'message': 'Successfully opted out of analytics'})
        
    except VisitorSession.DoesNotExist:
        return Response(
            {'error': 'Invalid session'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring
    """
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat()
    })
