from django.contrib import admin
from .models import Movie, Review, Petition, PetitionUpvote

class MovieAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']

class PetitionAdmin(admin.ModelAdmin):
    list_display = ['movie_title', 'created_by', 'upvotes', 'created_at']
    list_filter = ['created_at']
    search_fields = ['movie_title', 'created_by__username']
    readonly_fields = ['created_at', 'upvotes']
    ordering = ['-upvotes', '-created_at']

class PetitionUpvoteAdmin(admin.ModelAdmin):
    list_display = ['petition', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['petition__movie_title', 'user__username']
    ordering = ['-created_at']

admin.site.register(Movie, MovieAdmin)
admin.site.register(Review)
admin.site.register(Petition, PetitionAdmin)
admin.site.register(PetitionUpvote, PetitionUpvoteAdmin)