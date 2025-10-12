from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='cart.index'),
    path('<int:id>/add/', views.add, name='cart.add'),
    path('clear/', views.clear, name='cart.clear'),
    path('purchase/', views.purchase, name='cart.purchase'),
    path('customer-feedback/', views.customer_feedback_list, name='cart.customer_feedback'),
    path('submit-feedback/', views.submit_feedback, name='cart.submit_feedback'),
]