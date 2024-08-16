# blink/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Route the root URL to the index view
    path('video_feed/', views.video_feed, name='video_feed'),
    path('get_final_message/', views.get_final_message, name='get_final_message'),
]
