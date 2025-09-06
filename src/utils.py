def clean_text(text: str) -> str:
    """Strip whitespace and normalize spaces."""
    return " ".join(text.split()) if text else ""

def split_items(text: str):
    """Split comma or newline separated values into a list."""
    if not text:
        return []
    return [clean_text(item) for item in text.replace("\n", ",").split(",") if item.strip()]