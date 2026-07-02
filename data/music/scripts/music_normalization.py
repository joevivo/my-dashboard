import unicodedata


def normalize_text(value):
    text = str(value or "").lower()

    replacements = {
        "ü": "u",
        "ö": "o",
        "ä": "a",
        "é": "e",
        "è": "e",
        "á": "a",
        "à": "a",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
        "ç": "c",
    }

    for source, target in replacements.items():
        text = text.replace(source, target)

    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch for ch in text if ch.isalnum())
