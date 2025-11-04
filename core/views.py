"""
Authentication Views for Museum Staff
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from core.forms import MuseumRegistrationForm, StaffRegistrationForm, StaffLoginForm
from core.models import Museum, MuseumStaff, Artwork, Artist


def register_view(request):
    """Combined registration view for museum and staff"""
    if request.method == 'POST':
        museum_form = MuseumRegistrationForm(request.POST, request.FILES)
        staff_form = StaffRegistrationForm(request.POST)
        
        if museum_form.is_valid() and staff_form.is_valid():
            try:
                with transaction.atomic():
                    # Create museum
                    museum = museum_form.save()
                    
                    # Create staff account
                    staff = staff_form.save(commit=False)
                    staff.museum = museum
                    staff.role = 'admin'  # First user is admin
                    staff.save()
                    
                    # Log the user in
                    login(request, staff)
                    messages.success(request, f'Welcome to ArtScope, {staff.get_full_name()}!')
                    return redirect('dashboard')  # You'll need to create this view
                    
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        museum_form = MuseumRegistrationForm()
        staff_form = StaffRegistrationForm()
    
    return render(request, 'auth/register.html', {
        'museum_form': museum_form,
        'staff_form': staff_form,
    })


def login_view(request):
    """Login view for museum staff"""
    if request.method == 'POST':
        form = StaffLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = StaffLoginForm()
    
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('index')


@login_required
def dashboard_view(request):
    """Dashboard for logged-in museum staff"""
    museum = request.user.museum
    artworks = museum.artworks.all()[:10]
    
    context = {
        'museum': museum,
        'artworks': artworks,
        'total_artworks': museum.artworks.count(),
        'active_artworks': museum.artworks.filter(is_on_display=True).count(),
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def upload_artwork_view(request):
    """Page to upload new artwork"""
    return render(request, 'upload_artwork.html')


@login_required
@require_http_methods(["POST"])
def upload_artwork_submit(request):
    """Handle artwork upload with multiple images and GPS location"""
    try:
        # Get form data
        title = request.POST.get('title')
        artist_name = request.POST.get('artist')
        description = request.POST.get('description')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        geofence_radius = request.POST.get('geofence_radius_meters', 100)
        
        # Validation
        if not all([title, artist_name, description, latitude, longitude]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get or create artist
        artist, created = Artist.objects.get_or_create(
            name=artist_name,
            defaults={'biography': f'Artist of {title}'}
        )
        
        # Get museum from logged-in staff
        museum = request.user.museum
        
        # Count images
        image_count = int(request.POST.get('image_count', 0))
        if image_count == 0:
            return JsonResponse({'error': 'At least one image is required'}, status=400)
        
        # Create artwork with first image
        first_image = request.FILES.get('image_0')
        if not first_image:
            return JsonResponse({'error': 'No images uploaded'}, status=400)
        
        artwork = Artwork.objects.create(
            museum=museum,
            artist=artist,
            title=title,
            description=description,
            latitude=float(latitude),
            longitude=float(longitude),
            geofence_radius_meters=int(geofence_radius),
            image=first_image,
            is_on_display=True
        )
        
        # TODO: Handle additional images if needed (can create separate ArtworkImage model)
        # For now, only the first image is saved to the main Artwork model
        
        return JsonResponse({
            'success': True,
            'artwork_id': str(artwork.id),
            'message': 'Artwork uploaded successfully! Translations are being generated in the background.'
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger('artscope')
        logger.error(f'Upload failed: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_artwork_view(request, artwork_id):
    """Delete an artwork"""
    try:
        # Get the artwork
        artwork = Artwork.objects.get(id=artwork_id)
        
        # Check if user has permission (must be from same museum)
        if artwork.museum != request.user.museum:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Store title for response
        artwork_title = artwork.title
        
        # Delete the artwork (this will also delete the image file)
        artwork.delete()
        
        messages.success(request, f'Artwork "{artwork_title}" deleted successfully!')
        
        return JsonResponse({
            'success': True,
            'message': f'Artwork "{artwork_title}" deleted successfully'
        })
        
    except Artwork.DoesNotExist:
        return JsonResponse({'error': 'Artwork not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def edit_artwork_view(request, artwork_id):
    """Edit artwork page"""
    try:
        artwork = Artwork.objects.get(id=artwork_id)
        
        # Check if user has permission
        if artwork.museum != request.user.museum:
            messages.error(request, 'Permission denied')
            return redirect('dashboard')
        
        if request.method == 'POST':
            try:
                # Get form data
                title = request.POST.get('title')
                artist_name = request.POST.get('artist')
                description = request.POST.get('description')
                latitude = request.POST.get('latitude')
                longitude = request.POST.get('longitude')
                geofence_radius = request.POST.get('geofence_radius_meters', 100)
                is_on_display = request.POST.get('is_on_display') == 'on'
                
                # Update artist
                if artist_name != artwork.artist.name:
                    artist, created = Artist.objects.get_or_create(
                        name=artist_name,
                        defaults={'biography': f'Artist of {title}'}
                    )
                    artwork.artist = artist
                
                # Update artwork fields
                artwork.title = title
                artwork.description = description
                artwork.latitude = float(latitude)
                artwork.longitude = float(longitude)
                artwork.geofence_radius_meters = int(geofence_radius)
                artwork.is_on_display = is_on_display
                
                # Handle image replacement
                if 'image' in request.FILES:
                    artwork.image = request.FILES['image']
                
                artwork.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Artwork updated successfully'
                })
                
            except Exception as e:
                import logging
                logger = logging.getLogger('artscope')
                logger.error(f'Update failed: {str(e)}')
                return JsonResponse({'error': str(e)}, status=500)
        
        return render(request, 'edit_artwork.html', {'artwork': artwork})
        
    except Artwork.DoesNotExist:
        messages.error(request, 'Artwork not found')
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, str(e))
        return redirect('dashboard')


# ============================================
# NAVIGATION VIEWS
# ============================================

@login_required
def record_navigation_path_view(request):
    """
    Staff interface for recording navigation paths
    """
    from core.models import NavigationPath, NavigationWaypoint
    
    # Get staff's museum artworks for waypoint selection
    artworks = Artwork.objects.filter(museum=request.user.museum, is_on_display=True)
    
    # Get existing paths for this museum
    existing_paths = NavigationPath.objects.filter(museum=request.user.museum)
    
    return render(request, 'record_navigation_path.html', {
        'artworks': artworks,
        'existing_paths': existing_paths,
    })


def visitor_navigation_view(request):
    """
    Visitor interface for navigating to artworks
    Public view - no login required
    """
    return render(request, 'visitor_navigation.html')


@login_required
def upload_floor_map_view(request):
    """
    Staff interface for uploading floor maps and positioning artworks
    """
    return render(request, 'upload_floor_map.html')


def museum_map_view(request):
    """
    Interactive museum floor map with artwork pins
    Public view - no login required
    """
    return render(request, 'museum_map.html')
