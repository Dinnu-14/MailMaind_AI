"""NLP preprocessing pipeline for email classification."""
import re


def clean_text(text: str) -> str:
    """Preprocess raw email text: lowercase, strip URLs, normalize whitespaces."""
    if not text:
        return ""
    # Normalize unicode / whitespace
    text = text.lower()
    # Strip URL links
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    # Strip email addresses
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", " ", text)
    # Remove HTML tags if present
    text = re.sub(r"<.*?>", " ", text)
    # Remove non-alphanumeric punctuation except common hyphens
    text = re.sub(r"[^\w\s\-]", " ", text)
    # Normalize extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

