
from django.urls import path
from .views import safety_score

urlpatterns = [
    path("score/", safety_score, name="safety_score"),
]
