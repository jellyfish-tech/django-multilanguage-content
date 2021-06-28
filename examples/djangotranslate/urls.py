from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import SimpleSet

router = DefaultRouter()
router.register('simple', SimpleSet, basename='simple')


urlpatterns = [
    path('', include(router.urls))
]
