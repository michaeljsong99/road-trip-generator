from lookup import Lookup


class PathFinder:
    def __init__(self):
        self.lookup = Lookup()

    def filter_suggestions_on_distance(
        self, place_id, distance_remaining, suggestions, num_suggestions, from_city
    ):
        """
        Return a filtered list of suggestions that meet the distance constraint.
        :param place_id: The city or park origin place_id.
        :param distance_remaining: the max distance on the trip
        :param suggestions: the unfiltered list of potential destinations.
        :param num_suggestions: max number of suggestions in the filtered list.
        :param from_city: True if we start from a city, False if start from park.
        :return: A filtered list of suggestions.
        """
        # Now take the top num_suggestions of parks that satisfy the distance constraint.
        parks_found = 0
        top_suggestions = []
        for park_id in suggestions:
            if self.is_next_park_within_distance(
                distance_remaining=distance_remaining,
                origin_id=place_id,
                dest_id=park_id,
                from_city=from_city,
            ):
                top_suggestions.append(park_id)
                parks_found += 1
                if parks_found >= num_suggestions:
                    break
        return top_suggestions

    def is_next_park_within_distance(
        self, distance_remaining, origin_id, dest_id, from_city
    ):
        """
        We want to see if we can visit the next park while satisfying distance constraints.
        In order to be possible, it must be possible to drive to the next destination, and
        then from the next destination to a major city within distance_remaining.
        :param distance_remaining: The max. distance that is remaining on the road trip.
        :param origin_id: The place_id of the current park.
        :param dest_id: The place_id of the prospective next park.
        :param from_city: True if the origin is a city, False if it is a park.
        :return: True if possible, False if not.
        """
        if from_city:
            distance_to_next_park = self.lookup.distance_from_city_to_park(
                origin_id, dest_id
            )
        else:
            distance_to_next_park = self.lookup.distance_from_park_to_park(
                origin_id, dest_id
            )
        distance_from_next_park_to_city = self.lookup.distance_to_nearest_city(dest_id)
        return (
            distance_to_next_park + distance_from_next_park_to_city
            <= distance_remaining
        )

    def suggest_next_locations_from_park(
        self, place_id, unvisitable_parks, distance_remaining, num_suggestions=5
    ):
        """
        Suggest a list of num_suggestions next parks to visit.
        If no parks are possible, then return the nearest city instead.
        :param place_id: The place_id of the current park.
        :param unvisitable_parks: A set of parks that have been visited/eliminated already, for being too close.
        :param distance_remaining: The remaining distance on the road trip.
        :param num_suggestions: How many suggestions to return.
        :return: A dictionary with key either as "parks" or "city", and the value as a list of suggestions that
                    are returned, or a dict with the city name and distance if no parks are possible.
        """
        # Get the suggested parks.
        suggestions = self.lookup.suggestions_from_park(park_id=place_id)
        # Filter out the ones that are in the set of unvisitable parks.
        suggestions = [x for x in suggestions if x not in unvisitable_parks]
        top_suggestions = self.filter_suggestions_on_distance(
            place_id=place_id,
            distance_remaining=distance_remaining,
            suggestions=suggestions,
            num_suggestions=num_suggestions,
            from_city=False,
        )
        if top_suggestions:
            # We found at least one park.
            return {"parks": top_suggestions}
        else:
            nearest_city_name = self.lookup.nearest_city_name(place_id=place_id)
            distance_to_nearest_city = self.lookup.distance_to_nearest_city(
                place_id=place_id
            )
            info = {"name": nearest_city_name, "distance": distance_to_nearest_city}
            return {"city": info}

    def suggest_next_locations_from_city(
        self, city_name, distance_remaining, num_suggestions=5
    ):
        """
        Suggest a list of max num_suggestions parks to visit.
        :param city_name: The name of the starting city.
        :param distance_remaining: The maximum distance.
        :param num_suggestions: The maximum number of suggestions to return.
        :return: A dictionary with key of either "parks", or "error" if no parks were found.
        """
        city_id = self.lookup.lookup_city_id(city_name=city_name)
        suggestions = self.lookup.suggestions_from_city(city_id=city_id)
        top_suggestions = self.filter_suggestions_on_distance(
            place_id=city_id,
            distance_remaining=distance_remaining,
            suggestions=suggestions,
            num_suggestions=num_suggestions,
            from_city=True,
        )
        if top_suggestions:
            return {"parks": top_suggestions}
        else:
            return {
                "error": "Input distance was too small. Try expanding the input distance, or change the starting city."
            }


