def matches_keywords(keywords: list, text: str) -> list[str]:
    """Prüft, ob der Text eines der Keywords enthält"""
    import re

    text_lower = text.lower()
    matched_keywords = []

    for keyword in keywords:
        # Verwende Wortgrenzen (\b) für exakte Wort-Übereinstimmung
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
        if re.search(pattern, text_lower):
            matched_keywords.append(keyword)

    return matched_keywords
