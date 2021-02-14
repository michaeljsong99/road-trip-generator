from googlemaps import client

from google_maps_services import GMapsServices
from keys import API_KEY

g_client = client.Client(key=API_KEY)

g_maps_services = GMapsServices(client=g_client)
# g_maps_services.get_nps_raw_park_data()
# g_maps_services.fill_missing_park_data()
# g_maps_services.rank_places_by_reviews()
