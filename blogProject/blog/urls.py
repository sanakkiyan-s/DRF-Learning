from rest_framework import routers
from .views import BlogViewSet
from django.urls import path, include

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'blogs', BlogViewSet, basename='blog')


urlpatterns = [
    path('', include(router.urls)),
]