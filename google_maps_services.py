import urllib.request, json
from keys import NPS_API_KEY
import requests
from google_places import GPlaces

"""
A wrapper class than contains access to all the services in the Google Maps API.
"""


class GMapsServices:
    def __init__(self, client):
        # Services.
        self.g_places = GPlaces(client=client)

    def _get_photo_urls(self, photos):
        return [photo["url"] for photo in photos]

    # Get info for all national parks/monuments in USA. Makes request to National Park Services (NPS) API.
    def _get_usa_national_parks_request(self):
        # Configure API request
        # Note limit parameter is arbitrary value greater than total number of NPS sites
        endpoint = "https://developer.nps.gov/api/v1/parks?limit=600"
        params = {"api_key": NPS_API_KEY}
        response = requests.get(endpoint, params=params)
        data = (response.json())["data"]
        park_info = {}
        for park in data:
            name = park["fullName"]
            info = {}
            info["description"] = park[
                "description"
            ]  # A short description of the park.
            info["latitude"] = float(park["latitude"])
            info["longitude"] = float(park["longitude"])
            info["photos"] = self._get_photo_urls(park["images"])  # List of photo URLs.
            info["state"] = park["states"]  # Two letter state code
            info["designation"] = park[
                "designation"
            ]  # National Park, National Monument, National Preserve, etc.
            park_info[name] = info
        return park_info

    # Download photos of the national park sites locally.
    def _download_photos(self, park_info):
        keys = park_info.keys()
        num_parks = len(keys)
        park_index = 1
        for key in keys:
            photos = park_info[key]["photos"]
            index = 0
            for url in photos:
                # Only take the top 4 photos from each park.
                # Note that not all parks will have photos.
                if index > 3:
                    break
                file_name = f"photos/{key}_photo_{index}.jpg"
                with open(file_name, "wb") as handle:
                    response = requests.get(url, stream=True)
                    if not response.ok:
                        print(response)
                    else:
                        for block in response.iter_content(1024):
                            if not block:
                                break
                            handle.write(block)
                        index += 1
            print(
                f"Retrieved {index} photos for park {park_index} of {num_parks}: {key}."
            )
            park_index += 1

    def _get_google_data_for_parks(self, park_info):
        for key in park_info.keys():
            park = park_info[key]
            location_str = f"point:{park['latitude']},{park['longitude']}"
            query = f"{key}, {park['state']}"
            gplaces_response = self.g_places.search_for_places(query=query, location_bias=location_str)
            place = gplaces_response['candidates'][0]
            park['place_id']

    def get_all_national_parks(self, save_photos=False):
        # Later, this should also get ratings and number of ratings for all the parks using Google Places API.
        park_info = self._get_usa_national_parks_request()
        print(park_info)
        # Then, use requests to download all the photos.
        if save_photos:
            self._download_photos(park_info=park_info)
        # Now, use Google Places to get the place_id, rating, and user_ratings_total for each park.
        detailed_park_info = self._get_google_data_for_parks(park_info=park_info)
