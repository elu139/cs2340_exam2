from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, Rating, Petition, PetitionUpvote
from cart.models import Order, Item
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()

    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html', {'template_data': template_data})

def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie)
    
    # Get rating information
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(movie=movie, user=request.user)
        except Rating.DoesNotExist:
            user_rating = None

    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    template_data['user_rating'] = user_rating
    template_data['average_rating'] = movie.average_rating()
    template_data['total_ratings'] = movie.total_ratings()
    return render(request, 'movies/show.html', {'template_data': template_data})

@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)

    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html', {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('movies.show', id=id)

@login_required
def submit_rating(request, id):
    """Submit or update a rating for a movie"""
    if request.method == 'POST':
        movie = get_object_or_404(Movie, id=id)
        stars = request.POST.get('stars')
        
        if stars and stars.isdigit() and 1 <= int(stars) <= 5:
            # Update or create rating
            rating, created = Rating.objects.update_or_create(
                movie=movie,
                user=request.user,
                defaults={'stars': int(stars)}
            )
            
            if created:
                messages.success(request, f'Rating submitted: {stars} stars!')
            else:
                messages.success(request, f'Rating updated: {stars} stars!')
        else:
            messages.error(request, 'Invalid rating value.')
    
    return redirect('movies.show', id=id)

def petitions_index(request):
    """Display all movie petitions"""
    petitions_list = Petition.objects.all().order_by('-upvotes', '-created_at')

    # Pagination - 10 petitions per page
    paginator = Paginator(petitions_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get user's upvotes for display
    user_upvotes = set()
    if request.user.is_authenticated:
        upvotes = PetitionUpvote.objects.filter(user=request.user, petition__in=page_obj)
        user_upvotes = {upvote.petition.id for upvote in upvotes}

    template_data = {
        'title': 'Movie Petitions',
        'page_obj': page_obj,
        'user_upvotes': user_upvotes,
        'total_petitions': petitions_list.count()
    }
    return render(request, 'movies/petitions.html', {'template_data': template_data})

@login_required
def create_petition(request):
    """Create a new movie petition"""
    if request.method == 'GET':
        template_data = {
            'title': 'Create Movie Petition'
        }
        return render(request, 'movies/create_petition.html', {'template_data': template_data})

    elif request.method == 'POST':
        movie_title = request.POST.get('movie_title', '').strip()
        description = request.POST.get('description', '').strip()

        # Validation
        if not movie_title:
            messages.error(request, 'Movie title is required.')
            template_data = {
                'title': 'Create Movie Petition',
                'movie_title': movie_title,
                'description': description
            }
            return render(request, 'movies/create_petition.html', {'template_data': template_data})

        if not description:
            messages.error(request, 'Description is required.')
            template_data = {
                'title': 'Create Movie Petition',
                'movie_title': movie_title,
                'description': description
            }
            return render(request, 'movies/create_petition.html', {'template_data': template_data})

        # Create petition
        petition = Petition(
            movie_title=movie_title,
            description=description,
            created_by=request.user
        )
        petition.save()

        messages.success(request, f'Petition for "{movie_title}" created successfully!')
        return redirect('movies.petitions')

@login_required
def upvote_petition(request, petition_id):
    """Handle upvoting a petition via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        petition = get_object_or_404(Petition, id=petition_id)

        # Check if user already upvoted
        existing_upvote = PetitionUpvote.objects.filter(petition=petition, user=request.user).first()

        if existing_upvote:
            # Remove upvote (toggle off)
            existing_upvote.delete()
            petition.upvotes -= 1
            petition.save()

            return JsonResponse({
                'success': True,
                'message': 'Upvote removed!',
                'upvotes': petition.upvotes,
                'user_upvoted': False
            })
        else:
            # Add upvote
            try:
                new_upvote = PetitionUpvote(
                    petition=petition,
                    user=request.user
                )
                new_upvote.save()

                petition.upvotes += 1
                petition.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Petition upvoted!',
                    'upvotes': petition.upvotes,
                    'user_upvoted': True
                })

            except IntegrityError:
                return JsonResponse({'success': False, 'error': 'You have already upvoted this petition'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred while processing your upvote'}, status=500)

@login_required
def popularity_map(request):
    """Display the Local Popularity Map page"""
    template_data = {
        'title': 'Local Popularity Map'
    }
    return render(request, 'movies/popularity_map.html', {'template_data': template_data})

@login_required
def popularity_map_data(request):
    """API endpoint to get trending movies by state"""
    from accounts.models import UserProfile
    
    # Get all states with their top movies
    state_data = {}
    
    # Get all US states
    all_states = [state_code for state_code, state_name in UserProfile.US_STATES]
    
    for state_code in all_states:
        # Count movie purchases in this state using optimized query
        movie_counts = Item.objects.filter(
            order__user__userprofile__state=state_code
        ).values(
            'movie__id', 'movie__name'
        ).annotate(
            total_purchases=Count('id')
        ).order_by('-total_purchases')[:3]
        
        top_movies = []
        for idx, movie_data in enumerate(movie_counts):
            top_movies.append({
                'rank': idx + 1,
                'title': movie_data['movie__name'],
                'purchases': movie_data['total_purchases']
            })
        
        state_data[state_code] = {
            'state_name': dict(UserProfile.US_STATES)[state_code],
            'top_movies': top_movies
        }
    
    return JsonResponse(state_data)
