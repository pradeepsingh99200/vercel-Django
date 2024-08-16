# BlinkDetection/urls.py (or your project's root urls.py)
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blink.urls')),  # The root URL will now point to the blink app's URLs
]
