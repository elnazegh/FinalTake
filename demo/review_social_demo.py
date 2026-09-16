from backend.rating import Rating
from backend.review import Review


# Mock data until the database/backend is available
mock_user_id = 1
mock_media_id = 101
mock_media_title = "Interstellar"

review = None
rating = Rating(mock_user_id, mock_media_id)


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
    print("5. Exit")

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
            print("\n--- Your Review ---")
            print(f"Media: {mock_media_title}")
            print(f"Rating: {review.rating}/5.0")
            print(f"Review: {review.text}")

    elif choice == "5":
        print("Exiting FinalTake test.")
        break

    else:
        print("Invalid option.")
