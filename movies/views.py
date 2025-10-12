from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from .models import Movie, Review, Petition, PetitionUpvote
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError

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

    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
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

def petitions_index(request):
    """Display all movie petitions"""
    from .models import Petition, PetitionUpvote

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
    from .models import Petition

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
    from .models import Petition, PetitionUpvote

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