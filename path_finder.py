from lookup import Lookup


class PathFinder:
    def __init__(self):
        self.lookup = Lookup()

    def is_next_park_within_distance(self, distance_remaining, origin_id, dest_id):
        """
        We want to see if we can visit the next park while satisfying distance constraints.
        In order to be possible, it must be possible to drive to the next destination, and
        then from the next destination to a major city within distance_remaining.
        :param distance_remaining: The max. distance that is remaining on the road trip.
        :param origin_id: The place_id of the current park.
        :param dest_id: The place_id of the prospective next park.
        :return: True if possible, False if not.
        """
        distance_to_next_park = self.lookup.distance_from_park_to_park(
            origin_id, dest_id
        )
        distance_from_next_park_to_city = self.lookup.distance_to_nearest_city(dest_id)
        return (
            distance_to_next_park + distance_from_next_park_to_city
            <= distance_remaining
        )
