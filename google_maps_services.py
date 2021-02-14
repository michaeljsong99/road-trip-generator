import json
from keys import NPS_API_KEY
import requests
import pandas as pd
from google_places import GPlaces
from google_distance_matrix import GDistanceMatrix

"""
A wrapper class than contains access to all the services in the Google Maps API.
"""


class GMapsServices:
    def __init__(self, client):
        # Services.
        self.g_places = GPlaces(client=client)
        self.g_distance_matrix = GDistanceMatrix(client=client)

    def _get_photo_urls(self, photos):
        """
        Helper to get the actual photo urls in a list of photo dictionaries.
        :param photos: A list of dictionaries.
        :return: A list of strings, where each string is the photo's url.
        """
        return [photo["url"] for photo in photos]

    def _get_usa_national_parks_request(self):
        """
        # Get info for all national parks/monuments in USA. Makes request to National Park Services (NPS) API.
        :return: A dictionary containing the park names as keys, and its info as a value dictionary.
        """
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

    def _download_photos(self, park_info):
        """
        # Download photos of the national park sites locally.
        :param park_info: A dictionary containing park name, and other information (photos) as values in a dict.
        :return: None
        """
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

    def _get_google_data_for_cities(self):
        """
        Reading in the cities from the csv file, map each city to a Google place_id.
        :return: A dictionary of city name to place_id.
        """
        cities_to_place_id = {}
        df = pd.read_csv("data/us_cities.csv")
        df.reset_index(inplace=True)
        cities = list(df["city"])
        states = list(df["state_id"])
        for index, city in enumerate(cities):
            query = f"{city}, {states[index]}"
            print(f"Searching Google for {query}")
            gplaces_response = self.g_places.search_for_places(query=query)
            place = gplaces_response["candidates"][0]
            place_id = place["place_id"]
            cities_to_place_id[query] = place_id
        file_name = "data/cities_to_place_id.json"
        with open(file_name, "w") as fp:
            json.dump(cities_to_place_id, fp)
        return cities_to_place_id

    def _get_google_data_for_parks(self, park_info):
        """
        Given a dictionary of park information, get the Google place_id, reviews and number of reviews
        for each park.
        :param park_info: A dict containing the park name as key, and other info inside a value dict.
        :return: A new dictionary containing the additional Google fields.
        """
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

    def get_nearest_city_to_place(
        self, place_id, city_place_ids_to_parks_distances, place_ids_to_city
    ):
        """
        For each park, get the nearest city and distance to nearest city. Store in park_place_id_to_nearest_city.json
        :param place_id: The Google place_id of the park.
        :param city_place_ids_to_parks_distances: Dict where key is a city place_id, val is a dict of park place_ids and distances.
        :param place_ids_to_city: A dict mapping place_ids to city names.
        :return: A tuple containing the nearest dist (in km) and nearest city name.
        """
        nearest_dist = "N/A"
        nearest_city = "N/A"
        for city_id, distances in city_place_ids_to_parks_distances.items():
            try:
                distance = distances[place_id]
            except KeyError as ke:
                print(f"No route from park {place_id} to {place_ids_to_city[city_id]}")
                continue
            if distance == "N/A":
                continue
            elif nearest_dist == "N/A":
                nearest_dist = distance
                nearest_city = place_ids_to_city[city_id]
            else:
                if distance < nearest_dist:
                    nearest_dist = distance
                    nearest_city = place_ids_to_city[city_id]
        return nearest_dist, nearest_city

    def get_nps_raw_park_data(self, save_photos=False):
        """
        Make request to NPS API to get all park data. Saves data in data/nps_raw_park_data.json file.
        :param save_photos: Whether or not to save the photos to local disk.
        :return: A dictionary containing all the park information available from NPS.
        """
        park_info = self._get_usa_national_parks_request()
        # Then, use requests to download all the photos.
        if save_photos:
            self._download_photos(park_info=park_info)
        file_name = "data/nps_raw_park_data.json"
        with open(file_name, "w") as fp:
            json.dump(park_info, fp)
        return park_info

    def get_all_national_parks(self, save_photos=False):
        """
        Get all park data from the NPS API, and get the Google place_ids, reviews, and number of reviews
        for each place. Save all this information in data/park_data.json.
        :param save_photos: whether or not to download the park photos from NPS to local disk.
        :return: None
        """
        park_info = self.get_nps_raw_park_data(save_photos=save_photos)

        # Now, use Google Places to get the place_id, rating, and user_ratings_total for each park.
        detailed_park_info = self._get_google_data_for_parks(park_info=park_info)
        file_name = "data/park_data.json"
        with open(file_name, "w") as fp:
            json.dump(detailed_park_info, fp)

    def fill_missing_park_data(self):
        """
        # This method tries to find the parks that were not able to be found by Google.
        :return: None
        """
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

    def rank_places_by_reviews(self, limit=200):
        """
        Given a limit, retrieve the top {limit} places in the park_data.json file by number of reviews.
        :param limit: The top number of rows.
        :return: A list of the names of the top {limit} places.
        """
        with open("data/park_data.json") as f:
            park_data_with_google = json.load(f)
            park_data_with_google.pop(
                "Ellis Island Part of Statue of Liberty National Monument"
            )  # duplicate
            sorted_by_num_ratings = sorted(
                park_data_with_google.items(),
                key=lambda x: x[1]["num_ratings"],
                reverse=True,
            )
            for index, data in enumerate(sorted_by_num_ratings):
                print(
                    f"Rank: {index}, Ratings: {data[1]['num_ratings']}, Name: {data[0]}"
                )
            top_results = sorted_by_num_ratings[0:limit]
            return [data[0] for data in top_results]

    def map_place_id_to_cities(self):
        """
        Create a json mapping place_id to city based on the cities_to_place_id dictionary.
        :return: None
        """
        with open("data/cities_to_place_id.json") as f:
            city_to_place_id = json.load(f)
        place_id_to_city = {v: k for k, v in city_to_place_id.items()}
        file_name = "data/place_ids_to_city.json"
        with open(file_name, "w") as fp:
            json.dump(place_id_to_city, fp)

    def map_place_id_to_park_name(self):
        """
        Create a json mapping place_id to park based on the park_data dictionary.
        :return: None
        """
        with open("data/park_data.json") as f:
            park_to_info = json.load(f)
        place_id_to_park_name = {v["place_id"]: k for k, v in park_to_info.items()}
        file_name = "data/place_ids_to_park_name.json"
        with open(file_name, "w") as fp:
            json.dump(place_id_to_park_name, fp)

    def compute_nearest_city_for_each_park_place_id(self):
        """
        Create a dictionary that has the nearest city and distance to city for each park place_id.
        :return: None
        """
        with open("data/place_ids_to_city.json") as f:
            place_ids_to_city = json.load(f)
        with open("data/city_place_ids_to_parks_distances.json") as f2:
            city_to_park_distances = json.load(f2)
        with open("data/place_ids_to_park_name.json") as f3:
            place_ids_to_parks = json.load(f3)
        with open("data/park_distances.json") as f4:
            park_distances = json.load(f4)
        park_ids = list(park_distances.keys())

        park_id_to_nearest_city = {}
        for park_id in park_ids:
            nearest_dist, nearest_city = self.get_nearest_city_to_place(
                place_id=park_id,
                city_place_ids_to_parks_distances=city_to_park_distances,
                place_ids_to_city=place_ids_to_city,
            )
            park_id_to_nearest_city[park_id] = {
                "park_name": place_ids_to_parks[park_id],
                "distance_to_city": nearest_dist,
                "nearest_city": nearest_city,
            }
        file_name = "data/park_id_to_nearest_city.json"
        with open(file_name, "w") as fp:
            json.dump(park_id_to_nearest_city, fp)

    def compute_distances_for_cities(self, get_city_place_ids=False):
        """
        Computes the distance from each city to each park.
        :param get_city_place_ids: whether to call Google Places API to get the place_ids for each city.
        :return:
        """
        if get_city_place_ids:
            self._get_google_data_for_cities()
        self.g_distance_matrix.compute_cities_to_parks_distance()

    def compute_distances(self):
        """
        Make request to the Google Distance Matrix API to compute distances between the places.
        :return: None
        """
        top_places = self.rank_places_by_reviews()
        self.g_distance_matrix.build_distance_matrix(places=top_places)
