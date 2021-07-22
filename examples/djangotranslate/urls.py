from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SimpleSet

router = DefaultRouter()
router.register('simple', SimpleSet, basename='simple')


urlpatterns = [
    path('', include(router.urls))
]
