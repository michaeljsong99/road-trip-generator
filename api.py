# Flask API.
from flask import Flask, request
from flask_cors import CORS, cross_origin

from path_finder import PathFinder


app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


@app.route("/api")
@cross_origin()
def generate_path():
    """
    The request to generate a path.
    :return: A dictionary with (maximum) two fields:
        - 'result': will be 'ok' if a path was found, else an error message.
        - 'path': a list of start_city, parks, and end_city.
            - each element will have 'name' and 'next_distance' fields.
                for the end_city, the next_distance field represents the total distance driven.
            = parks will also have:
                - 'rating' => the avg. Google Rating.
                - 'num_reviews' => the total # of google reviews.
                - 'state' => the state the park is in.
                - 'photos' => a list of remote urls to the park's photos.
    """
    starting_city = request.args.get(
        "start_city"
    )  # A string representing the starting city.

    max_distance = float(
        request.args.get("max_distance")
    )  # The maximum driving distance (in kilometers).

    p = PathFinder()
    p.generate_path(starting_city=starting_city, max_distance=max_distance)
    return p.return_path()


# if __name__ == "__main__":
#     app.run(debug=True, port=8080)
