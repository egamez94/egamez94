from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .models import Park, Trip
from .forms import TripForm

# Create your views here.

class ParkListView(ListView):
    model = Park
    template_name = 'trips/park_list.html'
    context_object_name = 'parks'

class ParkDetailView(DetailView):
    model = Park
    template_name = 'trips/park_detail.html'
    context_object_name = 'park'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trips'] = Trip.objects.filter(park=self.object).order_by('-visit_date')
        return context

class TripCreateView(CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'trips/trip_form.html'
    success_url = reverse_lazy('trips:park_list') # Redirect to park list after successful submission
