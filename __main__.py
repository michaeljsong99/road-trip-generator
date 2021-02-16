from googlemaps import client

from google_maps_services import GMapsServices
from path_finder import PathFinder
from lookup import Lookup
from keys import API_KEY, NEW_API_KEY

g_client = client.Client(key=API_KEY)

g_maps_services = GMapsServices(client=g_client)
# g_maps_services.get_nps_raw_park_data()
# g_maps_services.fill_missing_park_data()
# top = g_maps_services.rank_places_by_reviews()
# print(top)
# g_maps_services.compute_distances_for_cities()
# g_maps_services.generate_relative_ratings()
# g_maps_services.rank_places_by_blended_rating()
# g_maps_services.suggest_next_parks()

# g_maps_services.park_ids_to_parks_within_distance()

# Testing
BRYCE_CANYON = "ChIJLevDAsZrNYcRBm2svvvY6Ws"
ZION = "ChIJ2fhEiNDqyoAR9VY2qhU6Lnw"

p = PathFinder()
print(p.is_next_park_within_distance(600, ZION, BRYCE_CANYON))
