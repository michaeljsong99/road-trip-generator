from googlemaps import client

from google_maps_services import GMapsServices
from keys import API_KEY

g_client = client.Client(key=API_KEY)

g_maps_services = GMapsServices(client=g_client)
g_maps_services.get_all_national_parks()
