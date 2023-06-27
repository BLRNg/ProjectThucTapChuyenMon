from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Movie(models.Model):
    title=models.CharField(max_length=70)
    genres=models.CharField(max_length=70)
    year=models.CharField(max_length=70)
    image=models.ImageField(upload_to="movie_image")
    movieduration=models.CharField(max_length=70)
    def __str__(self):
        return str(self.pk)
    
    def get_total_ratings(self):
        total_ratings = self.rating_set.count()
        return total_ratings
    
    def get_average_rating(self):
        average_rating = self.rating_set.aggregate(avg_rating=models.Avg('rating'))
        avg = average_rating['avg_rating']
        if avg is not None:
            rounded_avg = round(avg, 2)
            return rounded_avg
        return None
class Rating(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,default=None)
    movie=models.ForeignKey(Movie,on_delete=models.CASCADE,default=None)
    rating=models.CharField(max_length=70)
    rated_date=models.DateTimeField(auto_now_add=True)

