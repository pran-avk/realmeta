"""
Visitor Tracking Middleware
Captures anonymous analytics without PII
"""
from django.utils import timezone
from django.core.cache import cache
import uuid
import logging

logger = logging.getLogger('artscope')


class VisitorTrackingMiddleware:
    """
    Middleware to track visitor sessions anonymously
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get or create session ID
        session_id = request.COOKIES.get('artscope_session_id')
        
        if not session_id:
            session_id = str(uuid.uuid4())
            request.artscope_session_id = session_id
        else:
            request.artscope_session_id = session_id
        
        # Check if user has opted out
        opted_out = request.COOKIES.get('artscope_opt_out', 'false') == 'true'
        request.artscope_opted_out = opted_out
        
        # Process request
        response = self.get_response(request)
        
        # Set session cookie (if new)
        if not request.COOKIES.get('artscope_session_id'):
            response.set_cookie(
                'artscope_session_id',
                session_id,
                max_age=86400,  # 24 hours
                httponly=True,
                secure=True,
                samesite='Lax'
            )
        
        return response
