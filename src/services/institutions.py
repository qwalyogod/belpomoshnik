def _normalize(value: str | None) -> str:
    return (value or "").strip().casefold()


def _profile_locations(profile: dict) -> list[dict]:
    """Return every usable user location, with a flat-profile fallback."""
    locations = [
        location for location in (profile.get("locations") or [])
        if any((location.get(key) or "").strip() for key in ("region", "city", "district", "address"))
    ]
    if locations:
        return locations
    fallback = {
        "label": "Основной адрес",
        "region": profile.get("region", ""),
        "city": profile.get("city", ""),
        "district": profile.get("district", ""),
        "address": profile.get("address", ""),
        "is_primary": True,
    }
    if any((fallback.get(key) or "").strip() for key in ("region", "city", "district", "address")):
        return [fallback]
    return []


def has_profile_location(profile: dict) -> bool:
    return bool(_profile_locations(profile or {}))


def _location_label(location: dict) -> str:
    label = location.get("label") or "адрес"
    city = location.get("city") or location.get("settlement")
    district = location.get("district")
    region = location.get("region")
    parts = [part for part in (city, district, region) if part]
    if not parts:
        return label
    return f"{label}: {', '.join(parts[:2])}"


def _score_institution_for_location(institution: dict, location: dict) -> int:
    score = 0
    city = _normalize(institution.get("city") or institution.get("settlement"))
    region = _normalize(institution.get("region"))
    district = _normalize(institution.get("district"))

    location_city = _normalize(location.get("city") or location.get("settlement"))
    location_region = _normalize(location.get("region"))
    location_district = _normalize(location.get("district"))

    if location_city and city == location_city:
        score += 50
    if location_region and region == location_region:
        score += 24
    if location_district and district and district == location_district:
        score += 16
    if location_city and city and location_city in city:
        score += 6
    if location_region and not region:
        score += 1
    return score


def _institution_key(institution: dict) -> str:
    return str(
        institution.get("id")
        or institution.get("short_name")
        or institution.get("title")
        or institution.get("address")
        or id(institution)
    )


def _matches_query(institution: dict, query: str) -> bool:
    normalized_query = _normalize(query).replace("ё", "е")
    if not normalized_query:
        return True
    values = [
        institution.get("short_name", ""),
        institution.get("full_name", ""),
        institution.get("title", ""),
        institution.get("institution_type", ""),
        institution.get("city", ""),
        institution.get("settlement", ""),
        institution.get("district", ""),
        institution.get("region", ""),
        institution.get("address", ""),
        " ".join(institution.get("services", []) or []),
        " ".join(institution.get("tags", []) or []),
    ]
    haystack = _normalize(" ".join(str(value or "") for value in values)).replace("ё", "е")
    return normalized_query in haystack


def match_institutions(
    institutions: list[dict],
    profile: dict,
    institution_types: list[str] | tuple[str, ...] | set[str] | None,
    limit: int = 2,
) -> list[dict]:
    required_types = {_normalize(item) for item in (institution_types or []) if item}
    if not required_types:
        return []

    locations = _profile_locations(profile or {})

    scored: list[tuple[int, dict]] = []
    for institution in institutions:
        if not institution.get("is_active", True):
            continue
        if _normalize(institution.get("institution_type")) not in required_types:
            continue

        best_score = 1
        best_location = None
        for location in locations:
            location_score = _score_institution_for_location(institution, location)
            if location_score > best_score:
                best_score = location_score
                best_location = location

        item = institution.copy()
        if best_location:
            item["match_location"] = _location_label(best_location)
        scored.append((best_score, item))

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1].get("institution_type", ""),
            item[1].get("short_name", ""),
        )
    )
    return [item for _, item in scored[: max(0, limit)]]


def match_nearby_institutions(
    institutions: list[dict],
    profile: dict,
    query: str = "",
    limit: int = 10,
) -> list[dict]:
    """Find institutions near all user locations, not just the first address."""
    locations = _profile_locations(profile or {})
    if not locations:
        return []

    best_by_key: dict[str, tuple[int, dict]] = {}
    for institution in institutions:
        if not institution.get("is_active", True):
            continue
        if not _matches_query(institution, query):
            continue

        best_score = -1
        best_location = None
        for location in locations:
            location_score = _score_institution_for_location(institution, location)
            if location_score > best_score:
                best_score = location_score
                best_location = location
        if best_score < 0:
            continue

        item = institution.copy()
        if best_location:
            item["match_location"] = _location_label(best_location)
        item["nearby_score"] = best_score
        key = _institution_key(institution)
        current = best_by_key.get(key)
        if current is None or best_score > current[0]:
            best_by_key[key] = (best_score, item)

    scored = list(best_by_key.values())
    scored.sort(
        key=lambda item: (
            -item[0],
            item[1].get("city", ""),
            item[1].get("institution_type", ""),
            item[1].get("short_name", ""),
        )
    )
    return [item for _, item in scored[: max(0, limit)]]
