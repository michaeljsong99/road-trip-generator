# This class is a class that provides useful functions to look up information, while searching.
import json
import pandas as pd


class Lookup:
    def __init__(self):
        # Initialize all the lookup dictionaries.
        self._cities = pd.read_csv("data/us_cities.csv")
        with open("data/place_ids_to_city.json") as f:
            self._place_ids_to_city = json.load(f)
        with open("data/cities_to_place_id.json") as f2:
            self._cities_to_place_id = json.load(f2)
        with open("data/park_id_to_park_info.json") as f3:
            self._park_id_to_park_info = json.load(f3)
        with open("data/park_id_to_nearest_city.json") as f4:
            self._park_id_to_nearest_city = json.load(f4)
        with open("data/city_place_ids_to_parks_distances.json") as f5:
            self._city_to_park_distances = json.load(f5)
        with open("data/park_distances.json") as f6:
            self._park_distances = json.load(f6)
        with open("data/park_id_to_unvisitable_parks.json") as f7:
            self._park_id_to_unvisitable_parks = json.load(f7)
        with open("data/park_id_suggestions.json") as f8:
            self._park_id_to_suggestions = json.load(f8)
        with open("data/city_place_ids_to_park_suggestions.json") as f9:
            self._city_to_suggestions = json.load(f9)

    ##########################################
    # Simple lookups
    ##########################################
    def lookup_city_name(self, place_id):
        """
        Returns the city name of the place_id.
        :param place_id: the place_id of the city.
        :return: the city name.
        """
        return self._place_ids_to_city[place_id]

    def lookup_city_id(self, city_name):
        """
        Returns the place_id of the given city.
        :param city_name: The city name.
        :return: The city's place_id.
        """
        try:
            return self._cities_to_place_id[city_name]
        except LookupError as le:
            raise LookupError(f"Invalid city name {city_name} provided.")

    def lookup_park_name(self, place_id):
        """
        Returns the park name of the place_id.
        :param place_id: the place_id of the park.
        :return: the park name.
        """
        return self._park_id_to_park_info[place_id]["name"]

    def lookup_city_geocoordinates(self, city_name):
        """
        Returns the (latitude, longitude) of the given city.
        :param city_name: name of the city.
        :return: (latitude, longitude) tuple.
        """
        city_info = city_name.split(",")
        city, state = city_info[0], (city_info[1]).strip()
        row = (
            self._cities[(self._cities.city == city) & (self._cities.state_id == state)]
        ).iloc[0]
        return row["lat"], row["lng"]

    def lookup_park_geocoordinates(self, place_id):
        """
        Returns the (latitude, longitude) of the given park (as a a place_id).
        :param place_id: Park's place_id.
        :return: (latitude, longitude) tuple.
        """
        return (
            self._park_id_to_park_info[place_id]["latitude"],
            self._park_id_to_park_info[place_id]["longitude"],
        )

    def lookup_park_state(self, place_id):
        """
        Returns the state code the park is in.
        :param place_id: park's place_id
        :return: the two letter state code.
        """
        return self._park_id_to_park_info[place_id]["state"]

    def lookup_park_rating(self, place_id):
        """
        Returns the park's average google rating.
        :param place_id: park's place_id
        :return: average google rating (out of 5)
        """
        return self._park_id_to_park_info[place_id]["rating"]

    def lookup_park_num_ratings(self, place_id):
        """
        Returns the park's number of google ratings.
        :param place_id: park's place_id
        :return: number of google ratings
        """
        return self._park_id_to_park_info[place_id]["num_ratings"]

    def lookup_park_photos(self, place_id):
        """
        Returns the urls to the park's photos.
        :param place_id: park's place_id
        :return: a list of urls.
        """
        return self._park_id_to_park_info[place_id]["photos"]

    ##########################################
    # Distance-based lookups
    ##########################################
    def distance_to_nearest_city(self, place_id):
        """
        Returns the driving distance of a park to the nearest city.
        :param place_id: the place_id of the park
        :return: driving distance (in float) to nearest city. Could also be 'N/A'.
        """
        return self._park_id_to_nearest_city[place_id]["distance_to_city"]

    def nearest_city_name(self, place_id):
        """
        Returns the name of the nearest city to a park.
        :param place_id: the place_id of the park
        :return: Name of nearest city. Could also be 'N/A'.
        """
        return self._park_id_to_nearest_city[place_id]["nearest_city"]

    def distance_from_city_to_park(self, city_id, park_id):
        """
        Returns the driving distance from a given city to a given park.
        :param city_id: place_id of the city.
        :param park_id: place_id of the park.
        :return: The distance.
        """
        return self._city_to_park_distances[city_id][park_id]

    def distance_from_park_to_park(self, origin_id, dest_id):
        """
        Returns the driving distance from a given park to a given park.
        :param origin_id: place_id of the origin park.
        :param dest_id: place_id of the destination park.
        :return: The distance.
        """
        return self._park_distances[origin_id][dest_id]

    def parks_too_close_to_park_id(self, park_id):
        """
        Given a park's place_id, return a list of parks that are too close to the given park.
        :param park_id: place_id of the park.
        :return: A list of place_ids representing parks that are too close.
        """
        return self._park_id_to_unvisitable_parks[park_id]

    def suggestions_from_park(self, park_id):
        """
        Given a park's place_id, return a list of suggested next parks sorted by blended_rating/distance.
        :param park_id: place_id of the park.
        :return: list of place_ids of parks sorted by blended_rating/distance.
        """
        return self._park_id_to_suggestions[park_id]

    def suggestions_from_city(self, city_id):
        """
        Given a city's place_id, return a list of suggested next parks sorted by blended_rating/distance.
        :param city_id: place_id of the city.
        :return: list of place_ids of parks sorted by blended_rating/distance.
        """
        return self._city_to_suggestions[city_id]
