import random

from lookup import Lookup


class PathFinder:
    def __init__(self):
        self.lookup = Lookup()
        self.path = []  # List of road trip place_ids, starting and ending with cities.
        self.distances = []  # Distances travelled between each two points on the path.

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

    def select_park_from_list(self, parks):
        """
        Given a list of parks, choose one of them as the next destination. Parks near the front of the
        list should have a higher probability of being selected.
        :param parks: A list of park_ids, sorted in descending order of score.
        :return: The park id of the selected place.
        """
        # Given that the sum of the infinite series 1/2 + 1/4 + 1/8... = 1,
        # we assign each park a probability of 1/(2^i), where i is its position in the array (starting from 1).
        # For any remaining probability, we add it to the first park.
        probability_weights = []
        length = len(parks)
        for i in range(length):
            probability_weights.append(1 / 2 ** (i + 1))
        probability_weights[0] += 1 - sum(probability_weights)
        weights = tuple(probability_weights)
        selected_park = random.choices(parks, weights=weights, k=1)
        return selected_park[0]

    def suggest_next_locations_from_park(
        self,
        place_id,
        unvisitable_parks,
        distance_remaining,
        num_suggestions,
        unvisitable_states,
    ):
        """
        Suggest a list of num_suggestions next parks to visit.
        If no parks are possible, then return the nearest city instead.
        :param place_id: The place_id of the current park.
        :param unvisitable_parks: A set of parks that have been visited/eliminated already, for being too close.
        :param distance_remaining: The remaining distance on the road trip.
        :param num_suggestions: How many suggestions to return.
        :param unvisitable_states: A set of states that have been visited already.
        :return: A dictionary with key either as "parks" or "city", and the value as a list of suggestions that
                    are returned, or a dict with the city name and distance if no parks are possible.
        """
        # Get the suggested parks.
        suggestions = self.lookup.suggestions_from_park(park_id=place_id)
        # Filter out the ones that are in the set of unvisitable parks, or states.
        parks_too_close = set(self.lookup.parks_too_close_to_park_id(park_id=place_id))
        all_unvisitable_parks = unvisitable_parks.union(parks_too_close)
        suggestions = [x for x in suggestions if x not in all_unvisitable_parks]
        suggestions = [
            x
            for x in suggestions
            if (self.lookup.lookup_park_state(place_id=x)) not in unvisitable_states
        ]
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
        self, city_name, distance_remaining, num_suggestions
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

    def generate_path(self, starting_city, max_distance, num_suggestions=5):
        """
        Given a starting city and a path, generate a suggested road trip.
        :param starting_city: The name of the starting city.
        :param max_distance: The max driving distance for the road trip.
        :param num_suggestions: The max number of suggestions to return each time.
        :return: None. Store the path in self.path
        """
        # TODO: Later, support choosing the end city as well.
        starting_city_id = self.lookup.lookup_city_id(city_name=starting_city)
        self.path.append(starting_city_id)
        unvisitable_parks = set()
        unvisitable_states = set()
        initial_suggestion = True

        # Where we currently are.
        current_place = starting_city
        current_state = None
        # The distance we have remaining.
        distance_remaining = max_distance

        while True:
            print(unvisitable_states)
            if initial_suggestion:
                suggestions = self.suggest_next_locations_from_city(
                    city_name=current_place,
                    distance_remaining=max_distance,
                    num_suggestions=num_suggestions,
                )
            else:
                suggestions = self.suggest_next_locations_from_park(
                    place_id=current_place,
                    unvisitable_parks=unvisitable_parks,
                    distance_remaining=distance_remaining,
                    num_suggestions=num_suggestions,
                    unvisitable_states=unvisitable_states,
                )
            if "parks" not in suggestions:
                # Either no parks were found, or we reached the end city.
                if "error" in suggestions:
                    print(suggestions["error"])
                    raise RuntimeError("Invalid start city and distance input.")
                else:
                    # We reached the end city.
                    end_city_name = suggestions["city"]["name"]
                    end_city_id = self.lookup.lookup_city_id(city_name=end_city_name)
                    self.path.append(end_city_id)
                    distance = suggestions["city"]["distance"]
                    self.distances.append(distance)
                    return
            else:
                park_ids = suggestions["parks"]

                # Choose a destination in the list off of a given probability function.
                next_dest = self.select_park_from_list(parks=park_ids)
                next_dest_state = self.lookup.lookup_park_state(place_id=next_dest)
                if current_state is None:
                    current_state = next_dest_state
                self.path.append(next_dest)
                if initial_suggestion:
                    distance = self.lookup.distance_from_city_to_park(
                        city_id=starting_city_id, park_id=next_dest
                    )
                    initial_suggestion = False
                else:
                    distance = self.lookup.distance_from_park_to_park(
                        origin_id=current_place, dest_id=next_dest
                    )
                    # Add the parks nearby to unvisitable parks.
                    too_close_parks = self.lookup.parks_too_close_to_park_id(
                        park_id=current_place
                    )
                    for park in too_close_parks:
                        unvisitable_parks.add(park)
                    # Add the current park to unvisitable parks.
                    unvisitable_parks.add(current_place)

                self.distances.append(distance)
                distance_remaining -= distance

                # Set the current place to the next destination park.
                current_place = next_dest
                if next_dest_state != current_state:
                    unvisitable_states.add(current_state)
                    current_state = next_dest_state

    def describe_path(self):
        """
        Describe the path that was chosen.
        :return: None
        """
        if not self.path:
            print("No path was possible for the provided starting city and distance.")
            return

        ending_index = len(self.path) - 1
        for index, place in enumerate(self.path):
            if index == 0:
                print(f"Starting city: {self.lookup.lookup_city_name(place_id=place)}.")
                print(f"Distance to next destination: {self.distances[index]} km. \n")
            elif index == ending_index:
                print(f"Ending city: {self.lookup.lookup_city_name(place_id=place)}.")
                print(f"Total road trip driving distance: {sum(self.distances)} km.")
            else:
                print(f"Park #{index}: {self.lookup.lookup_park_name(place_id=place)}")
                print(f"State: {self.lookup.lookup_park_state(place_id=place)}")
                print(
                    f"Average Google Review: {self.lookup.lookup_park_rating(place_id=place)}"
                )
                print(
                    f"Number of Google Reviews: {self.lookup.lookup_park_num_ratings(place_id=place)}"
                )
                print(f"Distance to next destination: {self.distances[index]} km. \n")
