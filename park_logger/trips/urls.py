from django.urls import path
from .views import ParkListView, ParkDetailView, TripCreateView # Add TripCreateView

app_name = 'trips'

urlpatterns = [
    path('parks/', ParkListView.as_view(), name='park_list'),
    path('parks/<int:pk>/', ParkDetailView.as_view(), name='park_detail'),
    path('trip/add/', TripCreateView.as_view(), name='trip_add'), # New URL for adding trips
]
