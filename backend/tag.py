"""Validation and normalization for user-created review tags."""


def normalize_tags(tags):
    """Return unique, normalized tags in their original input order.

    Accept a comma-separated string or a list/tuple of tag strings.
    Tags are optional. Multi-word tags are preserved with single spaces.
    """
    if tags is None:
        return []

    if isinstance(tags, str):
        if not tags.strip():
            return []
        values = tags.split(",")
    elif isinstance(tags, (list, tuple)):
        values = tags
    else:
        raise ValueError("Tags must be text or a list of text tags.")

    normalized = []
    seen = set()

    for value in values:
        if not isinstance(value, str):
            raise ValueError("Each tag must be text.")
        if "," in value:
            raise ValueError("A single tag cannot contain a comma.")

        tag = " ".join(value.split()).casefold()
        if not tag:
            raise ValueError("Tags cannot be empty.")

        if tag not in seen:
            seen.add(tag)
            normalized.append(tag)

    return normalized