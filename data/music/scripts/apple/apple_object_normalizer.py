def clean_text(value):
    if not isinstance(value, str):
        return value

    try:
        repaired = value.encode("latin1").decode("utf-8")
        if "�" not in repaired:
            value = repaired
    except Exception:
        pass

    replacements = {
        "â€™": "’",
        "â€œ": "“",
        "â€": "”",
        "â€": "”",
        "â€“": "–",
        "â€”": "—",
        "â€¦": "…",
        "â„—": "℗",
    }

    for bad, good in replacements.items():
        value = value.replace(bad, good)

    return value


def normalize_apple_object(item, *, snapshot_id, captured_at, rank, source):
    attrs = item.get("attributes", {})
    play_params = attrs.get("playParams", {})

    return {
        "snapshotId": snapshot_id,
        "capturedAt": captured_at,
        "rank": rank,
        "appleId": item.get("id"),
        "objectType": item.get("type"),
        "name": clean_text(attrs.get("name")),
        "artistName": clean_text(attrs.get("artistName")),
        "releaseDate": attrs.get("releaseDate"),
        "genreNames": [clean_text(name) for name in (attrs.get("genreNames") or [])],
        "trackCount": attrs.get("trackCount"),
        "url": attrs.get("url"),
        "playParamsKind": play_params.get("kind"),
        "source": source
    }
