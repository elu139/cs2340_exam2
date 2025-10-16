from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg

class Movie(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='movie_images/')

    def __str__(self):
        return str(self.id) + ' - ' + self.name
    
    def average_rating(self):
        """Calculate and return the average rating for this movie"""
        avg = self.rating_set.aggregate(Avg('stars'))['stars__avg']
        return round(avg, 1) if avg else None
    
    def total_ratings(self):
        """Return the total number of ratings for this movie"""
        return self.rating_set.count()

class Review(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id) + ' - ' + self.movie.name

class Rating(models.Model):
    id = models.AutoField(primary_key=True)
    stars = models.IntegerField(choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)])
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('movie', 'user')  # One rating per user per movie

    def __str__(self):
        return f"{self.user.username} rated {self.movie.name} {self.stars} stars"

class Petition(models.Model):
    id = models.AutoField(primary_key=True)
    movie_title = models.CharField(max_length=255, help_text="Title of the movie to be added")
    description = models.TextField(help_text="Why this movie should be added to the catalog")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_petitions')
    created_at = models.DateTimeField(auto_now_add=True)
    upvotes = models.IntegerField(default=0)

    class Meta:
        ordering = ['-upvotes', '-created_at']

    def __str__(self):
        return f"Petition for '{self.movie_title}' by {self.created_by.username}"

class PetitionUpvote(models.Model):
    id = models.AutoField(primary_key=True)
    petition = models.ForeignKey(Petition, on_delete=models.CASCADE, related_name='upvote_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('petition', 'user')  # Prevent duplicate upvotes

    def __str__(self):
        return f"{self.user.username} upvoted '{self.petition.movie_title}'"
