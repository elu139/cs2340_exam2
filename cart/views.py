from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from movies.models import Movie
from .utils import calculate_cart_total
from .models import Order, Item, CustomerFeedback
import json

def index(request):
    cart_total = 0
    movies_in_cart = []
    cart = request.session.get('cart', {})
    movie_ids = list(cart.keys())
    if (movie_ids != []):
        movies_in_cart = Movie.objects.filter(id__in=movie_ids)
        cart_total = calculate_cart_total(cart, movies_in_cart)

    template_data = {}
    template_data['title'] = 'Cart'
    template_data['movies_in_cart'] = movies_in_cart
    template_data['cart_total'] = cart_total
    return render(request, 'cart/index.html', {'template_data': template_data})

def add(request, id):
    get_object_or_404(Movie, id=id)
    cart = request.session.get('cart', {})
    cart[id] = request.POST['quantity']
    request.session['cart'] = cart
    return redirect('cart.index')

def clear(request):
    request.session['cart'] = {}
    return redirect('cart.index')

@login_required
def purchase(request):
    cart = request.session.get('cart', {})
    movie_ids = list(cart.keys())

    if (movie_ids == []):
        return redirect('cart.index')
    
    movies_in_cart = Movie.objects.filter(id__in=movie_ids)
    cart_total = calculate_cart_total(cart, movies_in_cart)

    order = Order()
    order.user = request.user
    order.total = cart_total
    order.save()

    for movie in movies_in_cart:
        item = Item()
        item.movie = movie
        item.price = movie.price
        item.order = order
        item.quantity = cart[str(movie.id)]
        item.save()

    request.session['cart'] = {}
    template_data = {}
    template_data['title'] = 'Purchase confirmation'
    template_data['order_id'] = order.id
    template_data['show_feedback_popup'] = True  # Flag to trigger popup
    return render(request, 'cart/purchase.html', {'template_data': template_data})

def customer_feedback_list(request):
    """Display all customer feedback on a dedicated page"""
    feedback_list = CustomerFeedback.objects.all().order_by('-created_at')
    
    # Pagination - 10 feedback entries per page
    paginator = Paginator(feedback_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate summary statistics
    total_feedback = feedback_list.count()
    
    template_data = {
        'title': 'Customer Feedback',
        'page_obj': page_obj,
        'total_feedback': total_feedback,
    }
    return render(request, 'cart/customer_feedback.html', {'template_data': template_data})

@require_POST
def submit_feedback(request):
    """Handle AJAX submission of customer feedback"""
    try:
        # Parse JSON data from request
        data = json.loads(request.body)
        
        # Get order number from data
        order_id = data.get('order_id')
        if not order_id:
            return JsonResponse({
                'success': False,
                'error': 'Order ID is required.'
            }, status=400)
        
        # Get the order
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Order not found.'
            }, status=404)
        
        # Validate that feedback_text is not empty
        feedback_text = data.get('feedback_text', '').strip()
        if not feedback_text:
            return JsonResponse({
                'success': False,
                'error': 'Feedback text is required.'
            }, status=400)
        
        # Create feedback instance
        feedback = CustomerFeedback(
            name=data.get('name', '').strip() or None,
            feedback_text=feedback_text,
            order=order
        )
        feedback.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your feedback!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid data format.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while saving your feedback.'
        }, status=500)