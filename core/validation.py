def clean(text):
    if not text:
        return text
    return text.strip()[:500]
