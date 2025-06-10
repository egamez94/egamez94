import httpx
import json # For parsing JSON responses, though httpx can do .json()
from django.http import JsonResponse, HttpRequest
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .models import Park, Trip
from .forms import TripForm

# User-Agent for external API requests
USER_AGENT = "ParkLoggerApp/1.0 (parklogger@example.com)"
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"

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

class TripListView(ListView):
    model = Trip
    template_name = 'trips/trip_list.html'
    context_object_name = 'trips'
    queryset = Trip.objects.all().order_by('-visit_date')

class TripCreateView(CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'trips/trip_form.html'
    success_url = reverse_lazy('trips:park_list') # Redirect to park list after successful submission


async def ajax_get_nearby_parks(request: HttpRequest):
    if request.method == "GET":
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        location_query_str = request.GET.get('location_query')

        headers = {
            'User-Agent': USER_AGENT,
            'Accept-Language': 'en'
        }

        bounding_box = None
        overpass_area_id = None

        async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
            try:
                if lat and lon:
                    # 1. Reverse Geocoding to get bounding box or area ID
                    nominatim_url = f"{NOMINATIM_BASE_URL}/reverse"
                    params = {
                        'lat': lat, 'lon': lon, 'format': 'jsonv2', 
                        'addressdetails': '1', 'email': 'parklogger-admin@example.com'
                    }
                    response = await client.get(nominatim_url, params=params)
                    response.raise_for_status() # Raise an exception for HTTP errors 4xx/5xx
                    nominatim_data = response.json()
                    
                    if nominatim_data:
                        if 'boundingbox' in nominatim_data:
                            # s, n, w, e
                            bounding_box = nominatim_data['boundingbox'] 
                        # Could also try to get osm_id for an area (e.g., city) to use with Overpass area()
                        # For simplicity, using bounding_box first.
                        # Example: if nominatim_data.get('osm_type') == 'relation':
                        #    overpass_area_id = int(nominatim_data.get('osm_id', 0)) + 3600000000


                elif location_query_str:
                    # 2. Forward Geocoding to get bounding box
                    nominatim_url = f"{NOMINATIM_BASE_URL}/search"
                    params = {
                        'q': location_query_str, 'format': 'jsonv2', 
                        'addressdetails': '1', 'limit': '1', 'email': 'parklogger-admin@example.com'
                    }
                    response = await client.get(nominatim_url, params=params)
                    response.raise_for_status()
                    nominatim_data_list = response.json()
                    
                    if nominatim_data_list and isinstance(nominatim_data_list, list) and len(nominatim_data_list) > 0:
                        nominatim_data = nominatim_data_list[0]
                        if 'boundingbox' in nominatim_data:
                             # s, n, w, e
                            bounding_box = nominatim_data['boundingbox']
                    else:
                        return JsonResponse({'error': 'Location not found or invalid response from Nominatim.'}, status=404)

                else:
                    return JsonResponse({'error': 'Latitude/Longitude or location query required.'}, status=400)

                # 3. Query Overpass API for parks
                if bounding_box:
                    if not (isinstance(bounding_box, list) and len(bounding_box) == 4):
                        return JsonResponse({'error': 'Invalid bounding box received from geocoding service.'}, status=500)
                    try:
                        # Ensure coordinates can be converted to float and basic sanity check
                        s_lat, n_lat, w_lon, e_lon = map(float, bounding_box)
                        if s_lat > n_lat or w_lon > e_lon: # Basic check, doesn't handle antimeridian
                             # More complex validation could be added if needed, but Nominatim usually provides valid bbox.
                             # For now, we'll trust Nominatim's output if it's structurally valid.
                             pass # Allowing it for now, Overpass might handle/clip it.
                    except ValueError:
                        return JsonResponse({'error': 'Bounding box coordinates are not valid numbers.'}, status=500)

                    overpass_query = f"""
                        [out:json][timeout:25];
                        (
                          nwr({s_lat},{w_lon},{n_lat},{e_lon})["leisure"="park"];
                          nwr({s_lat},{w_lon},{n_lat},{e_lon})["boundary"="national_park"];
                        );
                        out tags;
                    """
                elif overpass_area_id: # This part is less likely to be hit with current logic but good for future
                    overpass_query = f"""
                        [out:json][timeout:25];
                        area({overpass_area_id})->.searchArea;
                        (
                          nwr(area.searchArea)["leisure"="park"];
                          nwr(area.searchArea)["boundary"="national_park"];
                        );
                        out tags;
                    """
                else: # This case should ideally be caught earlier by "Could not determine a search area"
                    return JsonResponse({'error': 'No valid search area (bounding box or area ID) available to query Overpass.'}, status=404)
                
                # Ensure overpass_query was actually set if logic passed through above branches without error
                if not overpass_query: # Should be redundant due to the 'else' above but as a safeguard
                     return JsonResponse({'error': 'Failed to construct Overpass query due to missing area definition.'}, status=500)

                overpass_response = await client.post(OVERPASS_API_URL, data={'data': overpass_query.strip()})
                overpass_response.raise_for_status()
                overpass_data = overpass_response.json()
                
                parks = []
                if 'elements' in overpass_data:
                    seen_park_names = set()
                    for element in overpass_data['elements']:
                        if 'tags' in element and 'name' in element['tags']:
                            park_name = element['tags']['name']
                            if park_name not in seen_park_names:
                                parks.append({'name': park_name, 'id': element.get('id')}) # Send some ID too
                                seen_park_names.add(park_name)
                
                return JsonResponse({'parks': parks})

            except httpx.HTTPStatusError as exc:
                error_message = f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}"
                # Log the error server-side if possible: print(error_message)
                return JsonResponse({'error': f"Error communicating with external services: Status {exc.response.status_code}"}, status=502) # Bad Gateway
            except httpx.RequestError as exc:
                error_message = f"Request error occurred while asking {exc.request.url!r}: {exc!r}"
                # Log the error server-side: print(error_message)
                return JsonResponse({'error': "Network error connecting to external services."}, status=503) # Service Unavailable
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Error decoding JSON response from external services.'}, status=500)
            except Exception as e:
                # Log the error server-side: print(f"An unexpected error occurred: {e}")
                return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method. Only GET is allowed.'}, status=405)
