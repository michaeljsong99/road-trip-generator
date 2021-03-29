from googlemaps import places

TEXT_QUERY = "textquery"

"""
A class that makes requests to the Google Places API.
Documentation: 
Source Code: https://github.com/googlemaps/google-maps-services-python/blob/master/googlemaps/places.py
"""


class GPlaces:
    def __init__(self, client):
        # Pass in a Google Maps Services Client.
        self._client = client
        # Fields that we want to retrieve from Google for each park.
        self._fields = [
            "name",
            "place_id",
            "rating",
            "user_ratings_total",
        ]

    def search_for_places(self, query, location_bias="ipbias"):
        return places.find_place(
            client=self._client,
            fields=self._fields,
            input=query,
            input_type=TEXT_QUERY,
            location_bias=location_bias,
        )

    def search_for_parks(self, keyword, location):
        return places.places_nearby(
            client=self._client,
            keyword=keyword,
            location=location,
            type="park",
            radius=20,
        )
