import csv
import random
import datetime

from pprint import pprint
from django.conf import settings
from MovieRecommender.models import Movie,Rating
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker

MOVIE_METADATA_CSV = settings.DATA_DIR / "movies.csv"

User = get_user_model()

import re



def extract_year_from_title(movie_title):
    year_match = re.search(r'\((\d{4})\)', movie_title)

    if year_match:
        year = year_match.group(1)
        return year
    else:
        return None

def retrieve_substring(string):
    index = string.find("|")
    if index != -1:
        substring = string[:index].strip()
        return substring
    else:
        return string.strip()



def load_movie_data(limit=1, verbose=True):
    with open(MOVIE_METADATA_CSV, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        dataset = []
        for i, row in enumerate(reader):
            _id = row.get("movieId")
            try:
                _id = int(_id)
            except:
                _id = None
            # print(row.get('movieId'), row.get('title'), retrieve_substring(row.get('genres')), extract_year_from_title(row.get('title')))
           
            data = {
                "id": _id,
                "title": row.get('title'),
                "genres": retrieve_substring(row.get('genres')),
                "year": extract_year_from_title(row.get('title')),
                "movieduration": "2 hrs"
            }
            # print(data)
            dataset.append(data)
            if i + 1 > limit:
                break
        # return dataset
   
    movies_new = [Movie(**x) for x in dataset]
    movies_bulk = Movie.objects.bulk_create(movies_new, ignore_conflicts=True)
    print(f"New movies: {len(movies_bulk)}")
    print(f"Total movies: {Movie.objects.count()}")


def get_fake_profiles(count=10):
    fake = Faker()
    user_data = []
    for _ in range(count):
        profile = fake.profile()
        data = {
            "username": profile.get('username'),
            "email": profile.get('mail'),
            "is_active": True
        }
        if 'name' in profile:
            fname, lname = profile.get('name').split(" ")[:2]
            data['first_name'] = fname
            data['last_name'] = lname
        user_data.append(data)
    return user_data

def generate_users(count=10):
    profiles = get_fake_profiles(count=count)
    new_users = []
    for profile in profiles:
        new_users.append(
            User(**profile)
        )
    user_bulk = User.objects.bulk_create(new_users, ignore_conflicts=True)
    print(f"New users: {len(user_bulk)}")
    print(f"Total users: {User.objects.count()}")



def generate_fake_reviews(num_reviews):
   
    # Get all movies
    movies = Movie.objects.all()

    # Get all users
    users = User.objects.all()

    # Generate fake reviews
    for _ in range(num_reviews):
        # Select a random movie
        movie = random.choice(movies)

        # Select a random user
        user = random.choice(users)

        # Check if a rating for the same user and movie combination already exists
        if Rating.objects.filter(user=user, movie=movie).exists():
            continue  # Skip creating the rating

      
        # Generate a random rating (assuming rating is a string field)
        rating = random.choice([str(x) for x in range(1, 6)])

        # Create a new rating instance
        new_rating = Rating(user=user, movie=movie, rating=rating, rated_date=timezone.now())

        # Save the new rating
        new_rating.save()

        # Print the generated fake review
        print(f"Fake review created - Movie: {movie.title}, User: {user.username}, Rating: {rating}")

def update_zero_ratings():
    # Retrieve all ratings with a rating value of zero
    zero_ratings = Rating.objects.filter(rating='0')

    # Update the rating value for each zero rating
    for rating in zero_ratings:
        rating.rating = '5'  # Set the desired updated value
        rating.save()

