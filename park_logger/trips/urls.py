from django.urls import path
from .views import ParkListView, ParkDetailView, TripCreateView, ajax_get_nearby_parks, TripListView

app_name = 'trips'

urlpatterns = [
    path('', TripListView.as_view(), name='trip_list'),
    path('parks/', ParkListView.as_view(), name='park_list'),
    path('parks/<int:pk>/', ParkDetailView.as_view(), name='park_detail'),
    path('trip/add/', TripCreateView.as_view(), name='trip_add'), # New URL for adding trips
    path('ajax/get_nearby_parks/', ajax_get_nearby_parks, name='ajax_get_nearby_parks'),
]
