from django.shortcuts import render,HttpResponseRedirect
from django.contrib.auth import authenticate,login,logout,update_session_auth_hash
from django.contrib.auth.models import User,Group
from .forms import SignUpForm,AddMovieForm,LoginForm,AddRatingForm
from .models import Movie,Rating
from django.contrib import messages
import pandas as pd
from math import sqrt
import numpy as np
import matplotlib.pyplot as plt
from math import ceil
from surprise import KNNBasic
import heapq
from collections import defaultdict
from operator import itemgetter
from surprise import Dataset
from surprise import Reader
from django.utils import timezone

# Create your views here.

def filterMovieByGenre():
     #filtering by genres
    allMovies=[]
    genresMovie= Movie.objects.values('genres', 'id')
    genres= {item["genres"] for item in genresMovie}
    for genre in genres:
        movie=Movie.objects.filter(genres=genre)
        print(movie)
        n = len(movie)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allMovies.append([movie, range(1, nSlides), nSlides])
    params={'allMovies':allMovies }
    return params


def generateRecommendation(request):
    if request.user.is_authenticated:
        movie=Movie.objects.all()
        rating=Rating.objects.all()
        x=[] 
        y=[]
        A=[]
        B=[]
       
        #Rating Data Frames
        # print(rating)
        for item in rating:
            A=[item.user.id,item.movie,item.rating]
            B+=[A]
        rating_df=pd.DataFrame(B,columns=['userId','movieId','rating'])
        testSubject = request.user.id
        k = 10

        reader = Reader(rating_scale=(1, 5))  # Adjust the rating scale as per your dataset
        data = Dataset.load_from_df(rating_df[['userId', 'movieId', 'rating']], reader)
        trainSet = data.build_full_trainset()
        print("This is Train Set")
        # print(trainSet)
        sim_options = {'name': 'cosine',
                    'user_based': False
                    }

        model = KNNBasic(sim_options=sim_options)
        # print("This is model")
        # print(model)
        model.fit(trainSet)
        simsMatrix = model.compute_similarities()
        
        print(simsMatrix)
        testUserInnerID = trainSet.to_inner_uid(testSubject)
        print(testUserInnerID)
        # Get the top K items we rated
        testUserRatings = trainSet.ur[testUserInnerID]
        kNeighbors = heapq.nlargest(k, testUserRatings, key=lambda t: t[1])

        # Get similar items to stuff we liked (weighted by rating)
        candidates = defaultdict(float)

        candidates2 = defaultdict(float)
        for itemID, rating in kNeighbors:
            similarityRow = simsMatrix[itemID]
            
            for innerID, score in enumerate(similarityRow):
            
                candidates[innerID] += score * rating
                candidates2[innerID] += score 
                
        for itemID, ratingSum in sorted(candidates.items(), key=itemgetter(1), reverse=True):
            
            if candidates2[itemID] != 0:
                    candidates[itemID] = candidates[itemID] / candidates2[itemID]
            else:
                    candidates[itemID] = 0  # or handle the zero division case as per your requirement

            
                
            
        # Build a dictionary of stuff the user has already seen
        watched = {}
        for itemID, rating in trainSet.ur[testUserInnerID]:
            watched[itemID] = 1
        print(watched)    
        # Get top-rated items from similar users:
        movie_ids = [] 
        pos = 0
        for itemID, ratingSum in sorted(candidates.items(), key=itemgetter(1), reverse=True):
            
            if not itemID in watched:
                movieID = trainSet.to_raw_iid(itemID)
                movie_ids.append(movieID)
                print(movieID, ratingSum)
                pos += 1
                if (pos > 10):
                    break

        
       
        print(movie_ids)
        for item in movie: 
            if any(item.id == movie_obj.id for movie_obj in movie_ids):
                x=[item.id,item.title,item.movieduration,item.genres] 
                y+=[x]
        movies_df = pd.DataFrame(y,columns=['movieId','title','movieduration','genres'])
        
        recommender = movies_df
        print("We recommend:")
        print(movies_df)


       
       
        return recommender.to_dict('records')
            

            




def signup(request):
    if not request.user.is_authenticated:
        if request.method=='POST':
            fm=SignUpForm(request.POST)
            if fm.is_valid():
                user=fm.save()
                group=Group.objects.get(name='Editor')
                user.groups.add(group)
                messages.success(request,'Account Created Successfully!!!')
        else:
            if not request.user.is_authenticated:
                fm=SignUpForm()
        return render(request,'MovieRecommender/signup.html',{'form':fm})
    else:
        return HttpResponseRedirect('/home/')

def user_login(request):
    if not request.user.is_authenticated:
        if request.method=='POST':
            fm=LoginForm(request=request,data=request.POST)
            if fm.is_valid():
                uname=fm.cleaned_data['username']
                upass=fm.cleaned_data['password']
                user=authenticate(username=uname,password=upass)
                if user is not None:
                    login(request,user)
                    messages.success(request,'Logged in Successfully!!')
                    return HttpResponseRedirect('/dashboard/')
        else:
            fm=LoginForm()
        return render(request,'MovieRecommender/login.html',{'form':fm})
    else:
        return HttpResponseRedirect('/dashboard/')



def home(request):
    params=filterMovieByGenre()
    params['recommended']=generateRecommendation(request)
    return render(request,'MovieRecommender/home.html',params)

def addmovie(request):
    if request.user.is_authenticated:
        if request.method=='POST':
            fm=AddMovieForm(request.POST,request.FILES)
            if fm.is_valid():
                fm.save()
                messages.success(request,'Movie Added Successfully!!!')
        else:
            fm=AddMovieForm()
        return render(request,'MovieRecommender/addmovie.html',{'form':fm})
    else:
        return HttpResponseRedirect('/login/')


def dashboard(request):
    if request.user.is_authenticated: 
        params=filterMovieByGenre()
        params['user']=request.user
        params['watchedMovie'] = movie_watched(request)
        if request.method=='POST':
            userid=request.POST.get('userid')
            movieid=request.POST.get('movieid')
            movie=Movie.objects.all()
            u=User.objects.get(pk=userid)
            m=Movie.objects.get(pk=movieid)
            rfm=AddRatingForm(request.POST)
            params['rform']=rfm
            if rfm.is_valid():
                rat=rfm.cleaned_data['rating']
                count=Rating.objects.filter(user=u,movie=m).count()
                ratingInDb = Rating.objects.filter(user=u, movie=m).first()
                # Retrieve all movies for the specific user
                # moviesOfUser = Movie.objects.filter(rating__user=u)
                # print("watched movie")
                # print(moviesOfUser)
                if(count>0):
                    ratingInDb.rating = rat  # Set the desired updated value
                    ratingInDb.rated_date=timezone.now()
                    ratingInDb.save()
                    messages.warning(request,'You have already updated your review to'+' '+rat+' '+"star !!")
                    return render(request,'MovieRecommender/dashboard.html',params)
                action=Rating(user=u,movie=m,rating=rat)
                action.save()
                messages.success(request,'You have submitted'+' '+rat+' '+"star")
            return render(request,'MovieRecommender/dashboard.html',params)
        else:
            #print(request.user.id)
            rfm=AddRatingForm()
            params['rform']=rfm
            movie=Movie.objects.all()
            return render(request,'MovieRecommender/dashboard.html',params)
    else:
        return HttpResponseRedirect('/login/')
            
def user_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return HttpResponseRedirect('/login/')


def profile(request):
    if request.user.is_authenticated:
        #"select sum(rating) from Rating where user=request.user.id"
        r=Rating.objects.filter(user=request.user.id)
        totalReview=0
        for item in r:
            totalReview+=int(item.rating)
        #select count(*) from Rating where user=request.user.id"
        totalwatchedmovie=Rating.objects.filter(user=request.user.id).count()
        return render(request,'MovieRecommender/profile.html',{'totalReview':totalReview,'totalwatchedmovie':totalwatchedmovie})
    else:
        return HttpResponseRedirect('/login/')


def movie_watched(request):
    userid = request.user.id
    u=User.objects.get(pk=userid)
    moviesOfUser = Rating.objects.filter(user=u)
    return moviesOfUser


