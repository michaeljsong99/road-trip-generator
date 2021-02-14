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
                file_name = f"photos/{key[0].upper()}/{key}_photo_{index}.jpg"
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
        num_parks = len(park_info.keys())
        index = 1
        keys = list(park_info.keys())
        for key in keys:
            park = park_info[key]
            # location_str = f"point:{park['latitude']},{park['longitude']}"
            query = f"{key}, {park['state']}"
            print(f"Searching park {index}/{num_parks}: {key}")
            gplaces_response = self.g_places.search_for_places(query=query)
            try:
                place = gplaces_response["candidates"][0]
            except Exception as e:
                print(f"Could not find Google Place for {key}. Removing. \n")
                continue

            park["place_id"] = place["place_id"]
            if "rating" not in place:
                print(f"No rating for place {key}. Removing. \n")
                park_info.pop(key)
            else:
                park["rating"] = place["rating"]
                park["num_ratings"] = place["user_ratings_total"]
                print(f"Mapped to {place['name']} \n")
            index += 1
        return park_info

    def get_nps_raw_park_data(self, save_photos=False):
        # Later, this should also get ratings and number of ratings for all the parks using Google Places API.
        park_info = self._get_usa_national_parks_request()
        # Then, use requests to download all the photos.
        if save_photos:
            self._download_photos(park_info=park_info)
        file_name = "data/nps_raw_park_data.json"
        with open(file_name, "w") as fp:
            json.dump(park_info, fp)
        return park_info

    def get_all_national_parks(self, save_photos=False):
        park_info = self.get_nps_raw_park_data(save_photos=save_photos)

        # Now, use Google Places to get the place_id, rating, and user_ratings_total for each park.
        detailed_park_info = self._get_google_data_for_parks(park_info=park_info)
        file_name = "data/park_data.json"
        with open(file_name, "w") as fp:
            json.dump(detailed_park_info, fp)

    # This method tries to find the parks that were not able to be found by Google.
    def fill_missing_park_data(self):
        with open("data/nps_raw_park_data.json") as f:
            raw_park_data = json.load(f)
        with open("data/park_data.json") as f2:
            park_data_with_google = json.load(f2)
        parks_with_data = set(park_data_with_google.keys())
        all_parks = raw_park_data.keys()
        for park in all_parks:
            # A lot of missing places are small/unvisited anyways.
            # However, National parks should not be missing.
            if park not in parks_with_data and "National Park" in park:
                location = f"point:{raw_park_data[park]['latitude']}, {raw_park_data[park]['longitude']})"
                gplaces_response = self.g_places.search_for_places(
                    query=park, location_bias=location
                )
                place_id = gplaces_response["candidates"][0]["place_id"]
                if park == "Mammoth Cave National Park":
                    rating = 4.7
                    num_ratings = 8752
                else:
                    rating = gplaces_response["candidates"][0]["rating"]
                    num_ratings = gplaces_response["candidates"][0][
                        "user_ratings_total"
                    ]
                park_nps_info = raw_park_data[park]
                park_nps_info["place_id"] = place_id
                park_nps_info["rating"] = rating
                park_nps_info["num_ratings"] = num_ratings
                # Add to the park data with google dictionary.
                park_data_with_google[park] = park_nps_info
        # Because the Google Places API does not give great search results, some manual
        # adjustments are necessary
        park_data_with_google["Sequoia & Kings Canyon National Parks"][
            "num_ratings"
        ] = 10000
        park_data_with_google["North Cascades National Park"]["num_ratings"] = 762
        file_name = "data/park_data.json"
        # Make sure that you have max 4 photos per park. Also make sure each park has all 9 fields.
        parks_to_remove = []
        for key, info in park_data_with_google.items():
            if len(info.keys()) != 9:
                parks_to_remove.append(key)
                continue
            if len(info["photos"]) > 4:
                info["photos"] = info["photos"][:4]
        for park in parks_to_remove:
            park_data_with_google.pop(park)
        with open(file_name, "w") as fp:
            json.dump(park_data_with_google, fp)

    def rank_places_by_reviews(self):
        with open("data/park_data.json") as f:
            park_data_with_google = json.load(f)
            sorted_by_num_ratings = sorted(
                park_data_with_google.items(),
                key=lambda x: x[1]["num_ratings"],
                reverse=True,
            )
            print(sorted_by_num_ratings)
