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
def scan_artwork_combined(request):
    """
    Combined scanning: Geofencing + Image Recognition
    
    Step 1: Check GPS location (geofencing)
    Step 2: If within range, use image recognition to identify specific artwork
    
    POST data:
    - image: Artwork photo from camera
    - latitude: User's GPS latitude
    - longitude: User's GPS longitude
    - museum_id: Optional museum ID filter
    
    Returns:
    - Matched artwork with similarity score
    - Access status (allowed/denied based on geofence)
    """
    from core.geolocation_utils import check_geofence
    from embeddings.mobilenet_engine import mobilenet_engine
    
    # Validate required fields
    if 'image' not in request.FILES:
        return Response({'error': 'Image required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not request.data.get('latitude') or not request.data.get('longitude'):
        return Response({'error': 'GPS location required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_lat = float(request.data.get('latitude'))
        user_lon = float(request.data.get('longitude'))
        image_file = request.FILES['image']
        museum_id = request.data.get('museum_id')
        
        # STEP 1: Filter artworks by GPS location (geofencing)
        artworks_query = Artwork.objects.filter(is_on_display=True)
        if museum_id:
            artworks_query = artworks_query.filter(museum_id=museum_id)
        
        # Filter artworks with GPS and embeddings
        artworks_query = artworks_query.exclude(
            latitude__isnull=True
        ).exclude(
            longitude__isnull=True
        ).exclude(
            embedding__isnull=True
        )
        
        # Check geofencing for all artworks
        accessible_artworks = []
        for artwork in artworks_query:
            is_accessible, distance = check_geofence(
                user_lat, user_lon,
                float(artwork.latitude),
                float(artwork.longitude),
                artwork.geofence_radius_meters
            )
            
            if is_accessible:
                accessible_artworks.append({
                    'artwork': artwork,
                    'distance': distance
                })
        
        if not accessible_artworks:
            return Response({
                'error': 'No artworks within range',
                'message': 'You need to be near an artwork to scan it',
                'access_denied': True
            }, status=status.HTTP_403_FORBIDDEN)
        
        logger.info(f"Found {len(accessible_artworks)} accessible artworks within geofence")
        
        # STEP 2: Use image recognition to identify which artwork
        # Generate embedding for scanned image
        image_data = image_file.read()
        query_embedding = mobilenet_engine.generate_embedding(image_data)
        
        # Compare with accessible artworks only
        similarities = []
        for item in accessible_artworks:
            artwork = item['artwork']
            artwork_embedding = np.array(artwork.embedding)
            
            similarity = mobilenet_engine.compute_similarity(
                query_embedding,
                artwork_embedding
            )
            
            similarities.append({
                'artwork': artwork,
                'similarity': similarity,
                'distance_meters': item['distance']
            })
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        if not similarities:
            return Response({
                'error': 'No matching artwork found',
                'message': 'Cannot identify the artwork in the image'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get best match
        best_match = similarities[0]
        artwork = best_match['artwork']
        similarity_score = best_match['similarity']
        
        # Check similarity threshold (70% minimum)
        if similarity_score < 0.70:
            return Response({
                'error': 'Low confidence match',
                'message': 'Please take a clearer photo of the artwork',
                'similarity_score': float(similarity_score),
                'suggested_artworks': [
                    {
                        'id': str(s['artwork'].id),
                        'title': s['artwork'].title,
                        'similarity': float(s['similarity'])
                    }
                    for s in similarities[:3]
                ]
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Success! Return matched artwork
        serializer = ArtworkDetailSerializer(artwork)
        
        logger.info(f"Artwork matched: {artwork.title} (similarity: {similarity_score:.2f})")
        
        return Response({
            'success': True,
            'artwork': serializer.data,
            'similarity_score': float(similarity_score),
            'distance_meters': best_match['distance_meters'],
            'confidence': 'high' if similarity_score > 0.85 else 'medium',
            'scanning_method': 'geofencing + image_recognition',
            'alternatives': [
                {
                    'id': str(s['artwork'].id),
                    'title': s['artwork'].title,
                    'similarity': float(s['similarity'])
                }
                for s in similarities[1:4]  # Show top 3 alternatives
            ] if len(similarities) > 1 else []
        })
        
    except Exception as e:
        logger.error(f"Combined scan failed: {str(e)}")
        return Response({
            'error': str(e),
            'message': 'Scanning failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


class VisitorSessionViewSet(viewsets.ModelViewSet):
    """
    Visitor session management for anonymous tracking
    """
    queryset = VisitorSession.objects.all()
    serializer_class = VisitorSessionSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        """
        Create a new visitor session
        POST /api/sessions/
        {
            "museum_id": "uuid",
            "analytics_consent": true
        }
        """
        museum_id = request.data.get('museum_id')
        analytics_consent = request.data.get('analytics_consent', True)
        
        # Get museum or create default
        if museum_id:
            museum = get_object_or_404(Museum, id=museum_id)
        else:
            # Get first active museum as default
            museum = Museum.objects.filter(is_active=True).first()
            if not museum:
                return Response(
                    {'error': 'No active museum found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Create session
        session = VisitorSession.objects.create(
            museum=museum,
            analytics_consent=analytics_consent,
            session_start=timezone.now()
        )
        
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def check_geofence_access(request):
    """
    Check if user's location is within geofence of any artwork
    Primary scanning method - location-based access control
    
    POST data:
    - latitude: User's current latitude
    - longitude: User's current longitude
    - museum_id: Optional museum ID to filter artworks
    
    Returns:
    - accessible_artworks: List of artworks within geofence
    - nearest_artwork: Closest artwork if none accessible
    """
    from core.geolocation_utils import check_geofence, get_distance_message
    
    user_lat = request.data.get('latitude')
    user_lon = request.data.get('longitude')
    museum_id = request.data.get('museum_id')
    
    if not user_lat or not user_lon:
        return Response(
            {'error': 'Location coordinates required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
    except (ValueError, TypeError):
        return Response(
            {'error': 'Invalid coordinates'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Filter artworks
    artworks_query = Artwork.objects.filter(is_on_display=True)
    if museum_id:
        artworks_query = artworks_query.filter(museum_id=museum_id)
    
    # Filter artworks with GPS coordinates
    artworks_query = artworks_query.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    
    accessible_artworks = []
    nearest_artwork = None
    min_distance = float('inf')
    
    for artwork in artworks_query:
        is_accessible, distance = check_geofence(
            user_lat, user_lon,
            float(artwork.latitude), float(artwork.longitude),
            artwork.geofence_radius_meters
        )
        
        if is_accessible:
            accessible_artworks.append({
                'id': str(artwork.id),
                'title': artwork.title,
                'artist': artwork.artist.name if artwork.artist else 'Unknown',
                'image': artwork.image.url if artwork.image else None,
                'distance_meters': round(distance, 2),
                'description': artwork.description[:200]
            })
        
        # Track nearest artwork
        if distance < min_distance:
            min_distance = distance
            nearest_artwork = {
                'id': str(artwork.id),
                'title': artwork.title,
                'artist': artwork.artist.name if artwork.artist else 'Unknown',
                'distance_meters': round(distance, 2),
                'message': get_distance_message(distance, artwork.geofence_radius_meters)
            }
    
    # Sort by distance
    accessible_artworks.sort(key=lambda x: x['distance_meters'])
    
    return Response({
        'accessible_artworks': accessible_artworks,
        'nearest_artwork': nearest_artwork if not accessible_artworks else None,
        'total_accessible': len(accessible_artworks),
        'scanning_method': 'geofencing'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for monitoring"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'scanning_method': 'geofencing'
    })


# ============================================
# NAVIGATION API ENDPOINTS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_navigation_path(request):
    """
    Save a new navigation path with waypoints (Staff only)
    """
    from core.models import NavigationPath, NavigationWaypoint
    
    try:
        data = request.data
        museum = request.user.museum
        
        # Create navigation path
        path = NavigationPath.objects.create(
            museum=museum,
            name=data.get('name'),
            description=data.get('description', ''),
            created_by=request.user
        )
        
        waypoints_data = data.get('waypoints', [])
        total_distance = 0
        previous_waypoint = None
        
        for idx, wp_data in enumerate(waypoints_data):
            # Get artwork if specified
            artwork = None
            if wp_data.get('artwork_id'):
                from core.models import Artwork
                artwork = Artwork.objects.filter(id=wp_data['artwork_id'], museum=museum).first()
            
            waypoint = NavigationWaypoint.objects.create(
                museum=museum,
                artwork=artwork,
                latitude=wp_data['latitude'],
                longitude=wp_data['longitude'],
                floor_level=wp_data.get('floor_level', 1),
                room_name=wp_data.get('room_name', ''),
                title=wp_data['title'],
                description=wp_data.get('description', ''),
                voice_instruction=wp_data.get('voice_instruction', ''),
                sequence_order=idx,
                distance_to_next_meters=wp_data.get('distance_to_next', 0),
                estimated_walk_seconds=wp_data.get('estimated_walk_seconds', 0),
                created_by=request.user
            )
            
            # Link to previous waypoint
            if previous_waypoint:
                previous_waypoint.next_waypoint = waypoint
                previous_waypoint.save()
                total_distance += previous_waypoint.distance_to_next_meters
            
            previous_waypoint = waypoint
        
        # Update path with total distance and waypoint sequence
        path.total_distance_meters = total_distance
        path.waypoint_sequence = [str(wp.id) for wp in NavigationWaypoint.objects.filter(
            museum=museum, created_by=request.user
        ).order_by('sequence_order')]
        path.save()
        
        return Response({
            'success': True,
            'path_id': str(path.id),
            'waypoint_count': len(waypoints_data),
            'total_distance_meters': total_distance
        })
        
    except Exception as e:
        logger.error(f'Navigation path save failed: {str(e)}')
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_navigation_path(request):
    """
    Get navigation path to specific artwork
    """
    from core.models import Artwork, NavigationWaypoint, NavigationPath
    
    try:
        target_artwork_id = request.query_params.get('target')
        user_lat = float(request.query_params.get('lat'))
        user_lon = float(request.query_params.get('lon'))
        
        if not target_artwork_id:
            return Response({'error': 'target artwork_id required'}, status=400)
        
        artwork = get_object_or_404(Artwork, id=target_artwork_id)
        
        # Find waypoint closest to user's location
        from geopy.distance import geodesic
        nearest_waypoint = None
        min_distance = float('inf')
        
        for waypoint in NavigationWaypoint.objects.filter(museum=artwork.museum, is_active=True):
            distance = geodesic(
                (user_lat, user_lon),
                (float(waypoint.latitude), float(waypoint.longitude))
            ).meters
            
            if distance < min_distance:
                min_distance = distance
                nearest_waypoint = waypoint
        
        # Find waypoint closest to target artwork
        target_waypoint = None
        if artwork.artwork_waypoints.exists():
            target_waypoint = artwork.artwork_waypoints.first()
        else:
            # Find nearest waypoint to artwork
            min_art_distance = float('inf')
            for waypoint in NavigationWaypoint.objects.filter(museum=artwork.museum, is_active=True):
                distance = geodesic(
                    (float(artwork.latitude), float(artwork.longitude)),
                    (float(waypoint.latitude), float(waypoint.longitude))
                ).meters
                
                if distance < min_art_distance:
                    min_art_distance = distance
                    target_waypoint = waypoint
        
        # Build path from nearest_waypoint to target_waypoint
        waypoints_path = []
        current = nearest_waypoint
        visited = set()
        
        while current and current != target_waypoint and current.id not in visited:
            visited.add(current.id)
            waypoints_path.append({
                'id': str(current.id),
                'title': current.title,
                'latitude': float(current.latitude),
                'longitude': float(current.longitude),
                'floor_level': current.floor_level,
                'room_name': current.room_name,
                'description': current.description,
                'voice_instruction': current.voice_instruction,
                'distance_to_next_meters': current.distance_to_next_meters,
                'estimated_walk_seconds': current.estimated_walk_seconds,
                'video_url': current.video_360.url if current.video_360 else None,
                'thumbnail_url': current.thumbnail.url if current.thumbnail else None,
            })
            current = current.next_waypoint
        
        # Add target waypoint
        if target_waypoint:
            waypoints_path.append({
                'id': str(target_waypoint.id),
                'title': target_waypoint.title,
                'latitude': float(target_waypoint.latitude),
                'longitude': float(target_waypoint.longitude),
                'floor_level': target_waypoint.floor_level,
                'room_name': target_waypoint.room_name,
                'description': target_waypoint.description,
                'voice_instruction': target_waypoint.voice_instruction,
                'is_destination': True,
                'video_url': target_waypoint.video_360.url if target_waypoint.video_360 else None,
                'thumbnail_url': target_waypoint.thumbnail.url if target_waypoint.thumbnail else None,
            })
        
        return Response({
            'waypoints': waypoints_path,
            'total_waypoints': len(waypoints_path),
            'target_artwork': {
                'id': str(artwork.id),
                'title': artwork.title,
                'artist': artwork.artist.name if artwork.artist else 'Unknown',
                'image_url': artwork.image.url if artwork.image else None,
            }
        })
        
    except Exception as e:
        logger.error(f'Navigation path retrieval failed: {str(e)}')
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_nearest_waypoint(request):
    """
    Find nearest waypoint to user's GPS location
    """
    from core.models import NavigationWaypoint
    from geopy.distance import geodesic
    
    try:
        user_lat = float(request.query_params.get('lat'))
        user_lon = float(request.query_params.get('lon'))
        museum_id = request.query_params.get('museum_id')
        
        waypoints = NavigationWaypoint.objects.filter(
            museum_id=museum_id,
            is_active=True
        ) if museum_id else NavigationWaypoint.objects.filter(is_active=True)
        
        nearest = None
        min_distance = float('inf')
        
        for waypoint in waypoints:
            distance = geodesic(
                (user_lat, user_lon),
                (float(waypoint.latitude), float(waypoint.longitude))
            ).meters
            
            if distance < min_distance:
                min_distance = distance
                nearest = waypoint
        
        if nearest:
            return Response({
                'waypoint': {
                    'id': str(nearest.id),
                    'title': nearest.title,
                    'latitude': float(nearest.latitude),
                    'longitude': float(nearest.longitude),
                    'floor_level': nearest.floor_level,
                    'room_name': nearest.room_name,
                    'distance_meters': round(min_distance, 2),
                    'video_url': nearest.video_360.url if nearest.video_360 else None,
                }
            })
        
        return Response({'error': 'No waypoints found'}, status=404)
        
    except Exception as e:
        logger.error(f'Nearest waypoint search failed: {str(e)}')
        return Response({'error': str(e)}, status=500)
