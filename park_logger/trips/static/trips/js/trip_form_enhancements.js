document.addEventListener('DOMContentLoaded', () => {
    const locationQueryInput = document.getElementById('location_query');
    const findByLocationBtn = document.getElementById('find_parks_by_location_btn');
    const useCurrentLocationBtn = document.getElementById('use_current_location_btn');
    const nearbyParksDropdown = document.getElementById('nearby_parks_dropdown');
    const parkNameMainInput = document.getElementById('id_name'); // Assuming Django form field 'name' -> id_name
    const loadingIndicator = document.getElementById('parks_loading_indicator');
    const errorMessageDiv = document.getElementById('parks_error_message');

    const parksApiUrl = '/trips/ajax/get_nearby_parks/';

    function showLoading(isLoading) {
        loadingIndicator.style.display = isLoading ? 'block' : 'none';
    }

    function displayError(message) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = message ? 'block' : 'none';
    }

    function populateDropdown(parks) {
        nearbyParksDropdown.innerHTML = '<option value="">-- Select a park --</option>'; // Clear existing options
        if (parks && parks.length > 0) {
            parks.forEach(park => {
                const option = document.createElement('option');
                option.value = park.name; // Could use park.id if the main form is to save ID
                option.textContent = park.name;
                nearbyParksDropdown.appendChild(option);
            });
            nearbyParksDropdown.disabled = false;
            displayError('');
        } else {
            displayError('No parks found for this location.');
            nearbyParksDropdown.disabled = true;
        }
    }

    async function fetchNearbyParks(params) {
        showLoading(true);
        displayError('');
        nearbyParksDropdown.disabled = true;
        populateDropdown([]); // Clear previous results

        const url = new URL(parksApiUrl, window.location.origin);
        if (params.lat && params.lon) {
            url.searchParams.append('lat', params.lat);
            url.searchParams.append('lon', params.lon);
        } else if (params.location_query) {
            url.searchParams.append('location_query', params.location_query);
        } else {
            displayError('Invalid parameters for fetching parks.');
            showLoading(false);
            return;
        }

        try {
            const response = await fetch(url.toString());
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: `HTTP error ${response.status}` }));
                throw new Error(errorData.error || `HTTP error ${response.status}`);
            }
            const data = await response.json();
            if (data.error) {
                displayError(data.error);
                populateDropdown([]);
            } else if (data.parks) {
                populateDropdown(data.parks);
            }
        } catch (error) {
            console.error('Error fetching nearby parks:', error);
            displayError(error.message || 'Failed to fetch parks. Check console for details.');
            populateDropdown([]);
        } finally {
            showLoading(false);
        }
    }

    if (findByLocationBtn) {
        findByLocationBtn.addEventListener('click', () => {
            const query = locationQueryInput.value.trim();
            if (query) {
                fetchNearbyParks({ location_query: query });
            } else {
                displayError('Please enter a location query.');
            }
        });
    }

    if (useCurrentLocationBtn) {
        useCurrentLocationBtn.addEventListener('click', () => {
            if (navigator.geolocation) {
                showLoading(true);
                displayError('');
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        fetchNearbyParks({ 
                            lat: position.coords.latitude, 
                            lon: position.coords.longitude 
                        });
                    },
                    (error) => {
                        console.error('Geolocation error:', error);
                        let message = 'Error getting current location.';
                        switch(error.code) {
                            case error.PERMISSION_DENIED:
                                message = "User denied the request for Geolocation.";
                                break;
                            case error.POSITION_UNAVAILABLE:
                                message = "Location information is unavailable.";
                                break;
                            case error.TIMEOUT:
                                message = "The request to get user location timed out.";
                                break;
                            case error.UNKNOWN_ERROR:
                                message = "An unknown error occurred while trying to get location.";
                                break;
                        }
                        displayError(message);
                        showLoading(false);
                    }
                );
            } else {
                displayError('Geolocation is not supported by this browser.');
            }
        });
    }

    if (nearbyParksDropdown && parkNameMainInput) {
        nearbyParksDropdown.addEventListener('change', (event) => {
            if (event.target.value) {
                parkNameMainInput.value = event.target.value;
                // Optionally, you might want to set a hidden field with park ID if you use park.id in option value
            }
        });
    } else {
        if (!parkNameMainInput) {
            console.warn('Main park name input field (e.g., #id_name) not found. Pre-filling will not work.');
        }
    }
});
