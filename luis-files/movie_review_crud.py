"""Standalone in-memory CRUD for movie reviews. Not connected to the rest of the app."""

reviews = {}
_next_id = 1


def create_review(movie_title, rating, comment=""):
    global _next_id
    review = {"id": _next_id, "movie_title": movie_title, "rating": rating, "comment": comment}
    reviews[_next_id] = review
    _next_id += 1
    return review


def get_review(review_id):
    return reviews.get(review_id)


def list_reviews():
    return list(reviews.values())


def update_review(review_id, rating=None, comment=None):
    review = reviews.get(review_id)
    if review is None:
        return None
    if rating is not None:
        review["rating"] = rating
    if comment is not None:
        review["comment"] = comment
    return review


def delete_review(review_id):
    return reviews.pop(review_id, None) is not None


if __name__ == "__main__":
    r = create_review("Inception", 5, "Great movie")
    print("Created:", r)
    print("Read:", get_review(r["id"]))
    print("Updated:", update_review(r["id"], rating=4, comment="Still great"))
    print("All:", list_reviews())
    print("Deleted:", delete_review(r["id"]))
    print("All:", list_reviews())
