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
        return '|'.join(query_list)

    # Makes request to Google Distance Matrix API.
    def _distance_matrix_request(self, origin_list, destination_list):
        origin_str = self._create_places_string(origin_list)
        destination_str = self._create_places_string(destination_list)
        return distance_matrix.distance_matrix(client=self._client, origins=origin_str, destinations=destination_str)

    # Save a distance dict to json.
    def _save_distance_dict(self, distance_dict):
        file_name = "data/park_distances.json"
        with open(file_name, "w") as fp:
            json.dump(distance_dict, fp)
        print('Saved distances to json file.')

    def build_distance_matrix(self, read_existing_data=False, places=None):
        '''
        IMPORTANT!!!
        Google Distance Matrix API costs $4 usd 1000 elements; (origin, dest) pairs.
        It comes with $300 USD free credits to be spent in first 90 days.
        Places:
            200 places x 200 places = 40,000 elements = $160 USD. (new api key)
            70 cities x 200 places = 14,000 elements = $56 USD (old api key).
        '''

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
        place_ids = [park_data[park]['place_id'] for park in parks]
        print(parks)
        print(place_ids)
        length = len(place_ids)

        distance_dict = {}
        file_name = "data/park_distances.json"
        # In case we want to build on existing data, read from json.
        if read_existing_data:
            with open(file_name) as f:
                distance_dict = json.load(f)

        # Create requests in blocks of 10 x 10.
        block_length = 10
        y = 0
        while y < length:
            # As a precaution, save after each row.
            if y > 0:
                self._save_distance_dict(distance_dict)
            end_y = min(length, y+block_length)
            x = 0
            while x < length:
                print(f"Retrieving block with row {y}, column {x}.")
                end_x = min(length, x+block_length)
                rows = place_ids[y:end_y]
                cols = place_ids[x:end_x]

                try:
                    # Make the request to Google Distance Matrix API.
                    block_distance_matrix = self._distance_matrix_request(origin_list=rows, destination_list=cols)
                except Exception as e:
                    # In case the API breaks for whatever reason, we want to save what we have so far.
                    self._save_distance_dict(distance_dict)
                    print(f"Failed at: y = {y} and x = {x}.")
                    print(f"Next time, we can rerun starting from this block.")
                    raise Exception('Google Distance Matrix API failed.')

                matrix_rows = block_distance_matrix['rows']

                for row_index, row in enumerate(matrix_rows):
                    row_place_id = rows[row_index]
                    elements = row['elements']
                    for col_index, dest in enumerate(elements):
                        col_place_id = cols[col_index]
                        val = 'N/A'
                        # Check if it is possible to go from origin to destination.
                        if 'distance' in dest:
                            distance_in_metres = dest['distance']['value']
                            if distance_in_metres == 0:
                                # Same start and end point. Set to N/A.
                                val = 'N/A'
                            else:
                                distance_in_kilometers = distance_in_metres / 1000
                                val = distance_in_kilometers
                        if row_place_id in distance_dict:
                            distance_dict[row_place_id][col_place_id] = val
                        else:
                            distance_dict[row_place_id] = {col_place_id: val}
                x = end_x
            y = end_y

        self._save_distance_dict(distance_dict)
        print('Finished retrieving Distance Matrix Data.')







