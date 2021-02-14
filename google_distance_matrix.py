from googlemaps import distance_matrix
import json
import numpy as np

TEXT_QUERY = "textquery"

"""
A class that makes requests to the Google Distance Matrix API.
Documentation: https://developers.google.com/maps/documentation/distance-matrix/overview
Source Code: https://github.com/googlemaps/google-maps-services-python/blob/master/googlemaps/distance_matrix.py
"""


class GDistanceMatrix:
    def __init__(self, client):
        # Pass in a Google Maps Services Client.
        self._client = client

    # Returns the list of origins/destinations as a string.
    def _create_places_string(self, place_list):
        query_list = [f"place_id:{place_id}" for place_id in place_list]
        return "|".join(query_list)

    # Makes request to Google Distance Matrix API.
    def _distance_matrix_request(self, origin_list, destination_list):
        origin_str = self._create_places_string(origin_list)
        destination_str = self._create_places_string(destination_list)
        return distance_matrix.distance_matrix(
            client=self._client, origins=origin_str, destinations=destination_str
        )

    # Save a distance dict to json.
    def _save_distance_dict(self, distance_dict, file_name):
        with open(file_name, "w") as fp:
            json.dump(distance_dict, fp)
        print("Saved distances to json file.")

    def _block_distance_matrix_request(
        self, file_name, origin_ids, dest_ids, distance_dict=None
    ):
        if distance_dict is None:
            distance_dict = {}
        y_length = len(origin_ids)
        x_length = len(dest_ids)
        # Create requests in blocks of 10 x 10. Distance Matrix restricts max request size to 100 elements.
        block_length = 10
        y = 0
        while y < y_length:
            # As a precaution, save after each row.
            if y > 0:
                self._save_distance_dict(distance_dict, file_name=file_name)
            end_y = min(y_length, y + block_length)
            x = 0
            while x < x_length:
                print(f"Retrieving block with row {y}, column {x}.")
                end_x = min(x_length, x + block_length)
                rows = origin_ids[y:end_y]
                cols = dest_ids[x:end_x]

                try:
                    # Make the request to Google Distance Matrix API.
                    block_distance_matrix = self._distance_matrix_request(
                        origin_list=rows, destination_list=cols
                    )
                except Exception as e:
                    # In case the API breaks for whatever reason, we want to save what we have so far.
                    self._save_distance_dict(distance_dict, file_name=file_name)
                    print(f"Failed at: y = {y} and x = {x}.")
                    print(f"Next time, we can rerun starting from this block.")
                    raise Exception("Google Distance Matrix API failed.")

                matrix_rows = block_distance_matrix["rows"]

                for row_index, row in enumerate(matrix_rows):
                    row_place_id = rows[row_index]
                    elements = row["elements"]
                    for col_index, dest in enumerate(elements):
                        col_place_id = cols[col_index]
                        val = "N/A"
                        # Check if it is possible to go from origin to destination.
                        if "distance" in dest:
                            distance_in_metres = dest["distance"]["value"]
                            if distance_in_metres == 0:
                                # Same start and end point. Set to N/A.
                                val = "N/A"
                            else:
                                distance_in_kilometers = distance_in_metres / 1000
                                val = distance_in_kilometers
                        if row_place_id in distance_dict:
                            distance_dict[row_place_id][col_place_id] = val
                        else:
                            distance_dict[row_place_id] = {col_place_id: val}
                x = end_x
            y = end_y

        self._save_distance_dict(distance_dict, file_name=file_name)
        print("Finished retrieving Distance Matrix Data.")

    def compute_cities_to_parks_distance(self):
        """
        IMPORTANT!!!
        Google Distance Matrix API costs $4 usd 1000 elements; (origin, dest) pairs.
        It comes with $300 USD free credits to be spent in first 90 days.
        Places:
            200 places x 200 places = 40,000 elements = $160 USD. (new api key)
            70 cities x 200 places = 14,000 elements = $56 USD (old api key).
        DO NOT CALL THIS METHOD UNLESS YOU ARE 100% SURE ON HOW GCP BILLING WORKS!
        """
        input_val = input(
            "Are you sure you want to call this method (expensive GCP cost)? Enter Y to continue."
        )
        if input_val not in {"Y", "y"}:
            raise ValueError("Terminating as user did not confirm by entering 'Y'.")

        with open("data/park_distances.json") as f:
            park_distances = json.load(f)
        with open("data/cities_to_place_id.json") as f2:
            cities_to_place_id = json.load(f2)
        cities = list(cities_to_place_id.values())
        parks = list(park_distances.keys())
        file_name = "data/city_place_ids_to_parks_distances.json"
        self._block_distance_matrix_request(
            file_name=file_name, origin_ids=cities, dest_ids=parks
        )

    def build_distance_matrix(self, read_existing_data=False, places=None):
        """
        IMPORTANT!!!
        Google Distance Matrix API costs $4 usd 1000 elements; (origin, dest) pairs.
        It comes with $300 USD free credits to be spent in first 90 days.
        Places:
            200 places x 200 places = 40,000 elements = $160 USD. (new api key)
            70 cities x 200 places = 14,000 elements = $56 USD (old api key).
        DO NOT CALL THIS METHOD UNLESS YOU ARE 100% SURE ON HOW GCP BILLING WORKS!
        """
        input_val = input(
            "Are you sure you want to call this method (expensive GCP cost)? Enter Y to continue."
        )
        if input_val not in {"Y", "y"}:
            raise ValueError("Terminating as user did not confirm by entering 'Y'.")

        with open("data/park_data.json") as f:
            park_data = json.load(f)
        if places:
            # Only accept the places listed in places. Otherwise, remove from dictionary.
            place_set = set(places)
            all_places = list(park_data.keys())
            for place in all_places:
                if place not in place_set:
                    park_data.pop(place)

        parks = sorted(list(park_data.keys()))
        place_ids = [park_data[park]["place_id"] for park in parks]

        distance_dict = {}
        file_name = "data/park_distances.json"
        # In case we want to build on existing data, read from json.
        if read_existing_data:
            with open(file_name) as f:
                distance_dict = json.load(f)

        self._block_distance_matrix_request(
            file_name=file_name,
            origin_ids=place_ids,
            dest_ids=place_ids,
            distance_dict=distance_dict,
        )
