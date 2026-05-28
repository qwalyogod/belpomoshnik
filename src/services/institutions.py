def _normalize(value: str | None) -> str:
    return (value or "").strip().casefold()


def match_institutions(
    institutions: list[dict],
    profile: dict,
    institution_types: list[str] | tuple[str, ...] | set[str] | None,
    limit: int = 2,
) -> list[dict]:
    required_types = {_normalize(item) for item in (institution_types or []) if item}
    if not required_types:
        return []

    profile_region = _normalize(profile.get("region"))
    profile_city = _normalize(profile.get("city"))
    profile_district = _normalize(profile.get("district"))

    scored: list[tuple[int, dict]] = []
    for institution in institutions:
        if not institution.get("is_active", True):
            continue
        if _normalize(institution.get("institution_type")) not in required_types:
            continue

        score = 0
        city = _normalize(institution.get("city") or institution.get("settlement"))
        region = _normalize(institution.get("region"))
        district = _normalize(institution.get("district"))

        if profile_city and city == profile_city:
            score += 40
        if profile_region and region == profile_region:
            score += 20
        if profile_district and district and district == profile_district:
            score += 10
        if not city:
            score += 1

        scored.append((score, institution))

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1].get("institution_type", ""),
            item[1].get("short_name", ""),
        )
    )
    return [item for _, item in scored[: max(0, limit)]]
