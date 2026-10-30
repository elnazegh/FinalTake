
import pytest
from backend.review import Review


def test_non_owner_cannot_edit_review():
    review = Review(1, "1", 4.5, "Original review")

    with pytest.raises(PermissionError):
        review.edit_review(2, "Unauthorized edit")

    assert review.text == "Original review"


def test_non_owner_cannot_delete_review():
    review = Review(1, "1", 4.5, "Original review")

    with pytest.raises(PermissionError):
        review.delete_review(2)

    assert review.text == "Original review"


def test_owner_can_edit_review():
    review = Review(1, "1", 4.5, "Original review")

    review.edit_review(1, "Updated review")

    assert review.text == "Updated review"
