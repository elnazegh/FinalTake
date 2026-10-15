from backend.rating import Rating
from backend.review import Review
from backend.favorite import Favorites
from backend.comment import Comment
from backend.review_draft import ReviewDrafts


# Mock data until the database/backend is available
mock_user_id = 1
mock_media_id = 101
mock_media_title = "Interstellar"

review = None
active_review_id = None
next_review_id = 1
comments = []

rating = Rating(
    mock_user_id,
    mock_media_id
)

favorites = Favorites(
    mock_user_id
)

review_drafts = ReviewDrafts()


while True:
    print("\n--- FinalTake Rating Test ---")
    print(f"Media: {mock_media_title}")

    if rating.value is None:
        print("Current Rating: None")
    else:
        print(
            f"Current Rating: "
            f"{rating.value}/5.0"
        )

    print("\n1. Add/Change Rating")
    print("2. Delete Rating")
    print("3. Write/Submit Review")
    print("4. View Review")
    print("5. Edit Review")
    print("6. Delete Review")
    print("7. Add to Favorites")
    print("8. Remove from Favorites")
    print("9. View Favorite Status")
    print("10. Add Comment")
    print("11. Edit Comment")
    print("12. Delete Comment")
    print("13. View Review Draft")
    print("14. Clear Review Draft")
    print("15. Exit")

    choice = input(
        "\nChoose an option: "
    )

    if choice == "1":
        try:
            user_input = float(
                input(
                    "Enter rating "
                    "(0.5 - 5.0): "
                )
            )

            rating.set_rating(
                user_input
            )

            print(
                f"Rating saved: "
                f"{rating.value}/5.0"
            )

        except ValueError as error:
            print(
                f"Error: {error}"
            )

    elif choice == "2":
        if rating.value is None:
            print(
                "There is no rating "
                "to delete."
            )

        else:
            rating.delete_rating()

            print(
                "Rating deleted."
            )

    elif choice == "3":
        if rating.value is None:
            print(
                "You must rate this media "
                "before writing a review."
            )

        else:
            print(
                f"\nYour Rating: "
                f"{rating.value}/5.0"
            )

            print(
                "Maximum review length: "
                "5000 characters."
            )

            saved_draft = (
                review_drafts.get_draft(
                    mock_user_id,
                    mock_media_id
                )
            )

            if saved_draft is not None:
                print(
                    "\n--- Recovered "
                    "Review Draft ---"
                )

                if saved_draft:
                    print(
                        saved_draft
                    )
                else:
                    print(
                        "[Empty draft]"
                    )

                updated_text = input(
                    "\nEnter updated review "
                    "text (press Enter to "
                    "keep the recovered "
                    "draft): "
                )

                if updated_text == "":
                    review_text = (
                        saved_draft
                    )
                else:
                    review_text = (
                        updated_text
                    )

            else:
                print(
                    "Write your review below."
                )

                review_text = input(
                    "\nReview: "
                )

            try:
                review_drafts.save_draft(
                    mock_user_id,
                    mock_media_id,
                    review_text
                )

                print(
                    "Review draft autosaved."
                )

            except ValueError as error:
                print(
                    f"Error: {error}"
                )

                continue

            submit_choice = input(
                "Submit this review now? "
                "(y/n): "
            ).strip().lower()

            if submit_choice != "y":
                print(
                    "Review not submitted. "
                    "The autosaved draft "
                    "was kept."
                )

                continue

            try:
                new_review = Review(
                    mock_user_id,
                    mock_media_id,
                    rating.value,
                    review_text
                )

                # Replacing the review removes
                # comments associated with the
                # previous review.
                if (
                    active_review_id
                    is not None
                ):
                    comments = [
                        comment
                        for comment
                        in comments
                        if (
                            comment.review_id
                            != active_review_id
                        )
                    ]

                review = new_review

                active_review_id = (
                    next_review_id
                )

                next_review_id += 1

                review_drafts.clear_draft(
                    mock_user_id,
                    mock_media_id
                )

                print(
                    "\nReview submitted "
                    "successfully!"
                )

                print(
                    "Saved review draft "
                    "cleared."
                )

            except ValueError as error:
                print(
                    f"Error: {error}"
                )

                print(
                    "The autosaved draft was "
                    "kept so it can be "
                    "recovered later."
                )

    elif choice == "4":
        if review is None:
            print(
                "You have not written "
                "a review yet."
            )

        else:
            review_data = (
                review.to_dict()
            )

            if review_data is None:
                print(
                    "You have not written "
                    "a review yet."
                )

            else:
                print(
                    "\n--- Your Review ---"
                )

                print(
                    f"Media: "
                    f"{mock_media_title}"
                )

                print(
                    f"User ID: "
                    f"{review_data['user_id']}"
                )

                print(
                    f"Media ID: "
                    f"{review_data['media_id']}"
                )

                print(
                    f"Rating: "
                    f"{review_data['rating']}"
                    f"/5.0"
                )

                print(
                    f"Review: "
                    f"{review_data['text']}"
                )

                review_comments = [
                    comment
                    for comment in comments
                    if (
                        comment.review_id
                        == active_review_id
                        and
                        comment.to_dict()
                        is not None
                    )
                ]

                print(
                    "\n--- Comments ---"
                )

                if not review_comments:
                    print(
                        "No comments yet."
                    )

                else:
                    for (
                        index,
                        comment
                    ) in enumerate(
                        review_comments,
                        start=1
                    ):
                        comment_data = (
                            comment.to_dict()
                        )

                        print(
                            f"{index}. User "
                            f"{comment_data['user_id']}: "
                            f"{comment_data['text']}"
                        )

    elif choice == "5":
        if review is None:
            print(
                "You have not written "
                "a review yet."
            )

        else:
            print(
                f"\nCurrent Review: "
                f"{review.text}"
            )

            new_text = input(
                "Enter your updated "
                "review: "
            )

            try:
                review.edit_review(
                    mock_user_id,
                    new_text
                )

                print(
                    "Review updated "
                    "successfully!"
                )

            except (
                ValueError,
                PermissionError
            ) as error:
                print(
                    f"Error: {error}"
                )

    elif choice == "6":
        if review is None:
            print(
                "You have no review "
                "to delete."
            )

        else:
            try:
                review.delete_review(
                    mock_user_id
                )

                comments = [
                    comment
                    for comment in comments
                    if (
                        comment.review_id
                        != active_review_id
                    )
                ]

                review = None
                active_review_id = None

                print(
                    "Review deleted."
                )

            except PermissionError as error:
                print(
                    f"Error: {error}"
                )

    elif choice == "7":
        if favorites.add_favorite(
            mock_media_id
        ):
            print(
                f"{mock_media_title} "
                "added to Favorites."
            )
        else:
            print(
                f"{mock_media_title} "
                "is already in Favorites."
            )

    elif choice == "8":
        if favorites.remove_favorite(
            mock_media_id
        ):
            print(
                f"{mock_media_title} "
                "removed from Favorites."
            )
        else:
            print(
                f"{mock_media_title} "
                "is not currently "
                "in Favorites."
            )

    elif choice == "9":
        if favorites.is_favorited(
            mock_media_id
        ):
            print(
                f"{mock_media_title} "
                "is in your Favorites."
            )
        else:
            print(
                f"{mock_media_title} "
                "is not in your Favorites."
            )

    elif choice == "10":
        if (
            review is None
            or active_review_id is None
        ):
            print(
                "You need a review before "
                "adding a comment."
            )

        else:
            comment_text = input(
                "Enter your comment: "
            )

            try:
                comment = Comment(
                    user_id=mock_user_id,
                    review_id=active_review_id,
                    text=comment_text
                )

                comments.append(
                    comment
                )

                print(
                    "Comment added "
                    "successfully!"
                )

            except ValueError as error:
                print(
                    f"Error: {error}"
                )

    elif choice == "11":
        if (
            review is None
            or active_review_id is None
        ):
            print(
                "You need a review before "
                "editing a comment."
            )

        else:
            review_comments = [
                comment
                for comment in comments
                if (
                    comment.review_id
                    == active_review_id
                    and
                    comment.to_dict()
                    is not None
                )
            ]

            if not review_comments:
                print(
                    "There are no comments "
                    "to edit."
                )

            else:
                print(
                    "\n--- Comments ---"
                )

                for (
                    index,
                    comment
                ) in enumerate(
                    review_comments,
                    start=1
                ):
                    print(
                        f"{index}. User "
                        f"{comment.user_id}: "
                        f"{comment.text}"
                    )

                selection_input = input(
                    "Choose the comment "
                    "to edit: "
                )

                try:
                    selection = int(
                        selection_input
                    )

                except ValueError:
                    print(
                        "Invalid comment "
                        "selection."
                    )

                    continue

                if (
                    selection < 1
                    or selection
                    > len(review_comments)
                ):
                    print(
                        "Invalid comment "
                        "selection."
                    )

                    continue

                selected_comment = (
                    review_comments[
                        selection - 1
                    ]
                )

                new_text = input(
                    "Enter your updated "
                    "comment: "
                )

                try:
                    selected_comment.edit_comment(
                        user_id=mock_user_id,
                        new_text=new_text
                    )

                    print(
                        "Comment updated "
                        "successfully!"
                    )

                except (
                    ValueError,
                    PermissionError
                ) as error:
                    print(
                        f"Error: {error}"
                    )

    elif choice == "12":
        if (
            review is None
            or active_review_id is None
        ):
            print(
                "You need a review before "
                "deleting a comment."
            )

        else:
            review_comments = [
                comment
                for comment in comments
                if (
                    comment.review_id
                    == active_review_id
                    and
                    comment.to_dict()
                    is not None
                )
            ]

            if not review_comments:
                print(
                    "There are no comments "
                    "to delete."
                )

            else:
                print(
                    "\n--- Comments ---"
                )

                for (
                    index,
                    comment
                ) in enumerate(
                    review_comments,
                    start=1
                ):
                    print(
                        f"{index}. User "
                        f"{comment.user_id}: "
                        f"{comment.text}"
                    )

                selection_input = input(
                    "Choose the comment "
                    "to delete: "
                )

                try:
                    selection = int(
                        selection_input
                    )

                except ValueError:
                    print(
                        "Invalid comment "
                        "selection."
                    )

                    continue

                if (
                    selection < 1
                    or selection
                    > len(review_comments)
                ):
                    print(
                        "Invalid comment "
                        "selection."
                    )

                    continue

                selected_comment = (
                    review_comments[
                        selection - 1
                    ]
                )

                try:
                    selected_comment.delete_comment(
                        user_id=mock_user_id
                    )

                    comments.remove(
                        selected_comment
                    )

                    print(
                        "Comment deleted "
                        "successfully!"
                    )

                except (
                    ValueError,
                    PermissionError
                ) as error:
                    print(
                        f"Error: {error}"
                    )

    elif choice == "13":
        saved_draft = (
            review_drafts.get_draft(
                mock_user_id,
                mock_media_id
            )
        )

        if saved_draft is None:
            print(
                "There is no saved "
                "review draft."
            )

        else:
            print(
                "\n--- Saved Review Draft ---"
            )

            if saved_draft:
                print(
                    saved_draft
                )
            else:
                print(
                    "[Empty draft]"
                )

    elif choice == "14":
        if review_drafts.clear_draft(
            mock_user_id,
            mock_media_id
        ):
            print(
                "Review draft cleared."
            )
        else:
            print(
                "There is no saved review "
                "draft to clear."
            )

    elif choice == "15":
        print(
            "Exiting FinalTake test."
        )

        break

    else:
        print(
            "Invalid option."
        )
