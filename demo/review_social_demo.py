from backend.rating import Rating
from backend.review import Review
from backend.favorite import Favorites


# Mock data until the database/backend is available
mock_user_id = 1
mock_media_id = 101
mock_media_title = "Interstellar"

review = None
rating = Rating(mock_user_id, mock_media_id)
favorites = Favorites(mock_user_id)


while True:
    print("\n--- FinalTake Rating Test ---")
    print(f"Media: {mock_media_title}")

    if rating.value is None:
        print("Current Rating: None")
    else:
        print(f"Current Rating: {rating.value}/5.0")

    print("\n1. Add/Change Rating")
    print("2. Delete Rating")
    print("3. Write Review")
    print("4. View Review")
    print("5. Edit Review")
    print("6. Delete Review")
    print("7. Add to Favorites")
    print("8. Remove from Favorites")
    print("9. View Favorite Status")
    print("10. Exit")

    choice = input("\nChoose an option: ")

    if choice == "1":
        try:
            user_input = float(
                input("Enter rating (0.5 - 5.0): ")
            )

            rating.set_rating(user_input)

            print(
                f"Rating saved: {rating.value}/5.0"
            )

        except ValueError as error:
            print(f"Error: {error}")

    elif choice == "2":
        if rating.value is None:
            print("There is no rating to delete.")
        else:
            rating.delete_rating()
            print("Rating deleted.")

    elif choice == "3":
        if rating.value is None:
            print(
                "You must rate this media before writing a review."
            )

        else:
            print(f"\nYour Rating: {rating.value}/5.0")
            print("Write your review below.")
            print("Maximum length: 5000 characters.")

            review_text = input("\nReview: ")

            try:
                review = Review(
                    mock_user_id,
                    mock_media_id,
                    rating.value,
                    review_text
                )

                print("\nReview submitted successfully!")

            except ValueError as error:
                print(f"Error: {error}")

    elif choice == "4":
        if review is None:
            print("You have not written a review yet.")
        else:
            review_data = review.to_dict()

            if review_data is None:
                print("You have not written a review yet.")
            else:
                print("\n--- Your Review ---")
                print(f"Media: {mock_media_title}")
                print(f"User ID: {review_data['user_id']}")
                print(f"Media ID: {review_data['media_id']}")
                print(f"Rating: {review_data['rating']}/5.0")
                print(f"Review: {review_data['text']}")

    elif choice == "5":
        if review is None:
            print("You have not written a review yet.")
        else:
            print(f"\nCurrent Review: {review.text}")
            new_text = input("Enter your updated review: ")

            try:
                review.edit_review(
                    mock_user_id,
                    new_text
                )

                print("Review updated successfully!")

            except (ValueError, PermissionError) as error:
                print(f"Error: {error}")

    elif choice == "6":
        if review is None:
            print("You have no review to delete.")
        else:
            try:
                review.delete_review(mock_user_id)
                review = None
                print("Review deleted.")

            except PermissionError as error:
                print(f"Error: {error}")

    elif choice == "7":
        if favorites.add_favorite(mock_media_id):
            print(
                f"{mock_media_title} added to Favorites."
            )
        else:
            print(
                f"{mock_media_title} is already in Favorites."
            )

    elif choice == "8":
        if favorites.remove_favorite(mock_media_id):
            print(
                f"{mock_media_title} removed from Favorites."
            )
        else:
            print(
                f"{mock_media_title} is not currently in Favorites."
            )

    elif choice == "9":
        if favorites.is_favorited(mock_media_id):
            print(
                f"{mock_media_title} is in your Favorites."
            )
        else:
            print(
                f"{mock_media_title} is not in your Favorites."
            )

    elif choice == "10":
        print("Exiting FinalTake test.")
        break

    else:
        print("Invalid option.")