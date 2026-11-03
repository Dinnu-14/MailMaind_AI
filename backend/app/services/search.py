"""Keyword + lightweight natural-language email search."""
import re

from app.services.lexicon import CATEGORY_ALIASES, KEYWORD_ALIASES, keyword_hit

STOP = {"show", "me", "find", "emails", "email", "mails", "mail", "from", "about", "the", "all", "my", "any",
        "with", "regarding", "related", "to", "of", "for", "and", "a", "an", "please", "list", "get", "in", "on",
        "that", "are", "is", "have", "i", "do", "search", "look", "new", "latest", "recent", "notifications",
        "notification", "messages", "message", "opportunities", "opportunity"}


def _stem(w: str) -> str:
    for suf in ("ing", "ers", "er", "es", "s", "ed"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def parse_query(q: str) -> dict:
    text = " " + (q or "").lower().strip() + " "
    parsed = {"categories": [], "keywords": [], "unread": False, "priority": None, "important": None,
              "from_text": None, "tokens": []}
    if re.search(r"\bunread\b", text):
        parsed["unread"] = True
        text = re.sub(r"\bunread\b", " ", text)
    m = re.search(r"\b(high|medium|low)[- ]priority\b|\b(high|medium|low) priority\b", text)
    if m:
        parsed["priority"] = (m.group(1) or m.group(2)).title()
        text = text.replace(m.group(0), " ")
    if re.search(r"\b(important|urgent)\b", text):
        parsed["important"] = True
        text = re.sub(r"\b(important|urgent)\b", " ", text)
    m = re.search(r"\bfrom\s+([a-z0-9@._\- ]+?)(?=\s+(about|regarding|with|on|in)\b|\s*$)", text)
    if m:
        parsed["from_text"] = m.group(1).strip()
        text = text.replace(m.group(0), " ")
    for pattern, kw in KEYWORD_ALIASES:
        m = re.search(pattern, text)
        if m:
            parsed["keywords"].append(kw)
            text = text[: m.start()] + " " + text[m.end():]
    for pattern, cat in CATEGORY_ALIASES:
        m = re.search(pattern, text)
        if m:
            parsed["categories"].append(cat)
            text = text[: m.start()] + " " + text[m.end():]
    words = re.findall(r"[a-z0-9][a-z0-9.\-/']*", text)
    parsed["tokens"] = [_stem(w) for w in words if w not in STOP and len(w) > 1]
    return parsed


def describe(parsed: dict) -> str:
    bits = []
    if parsed["categories"]:
        bits.append("category: " + ", ".join(parsed["categories"]))
    if parsed["keywords"]:
        bits.append("topic: " + ", ".join(parsed["keywords"]))
    if parsed["from_text"]:
        bits.append(f"from: {parsed['from_text']}")
    if parsed["priority"]:
        bits.append(f"priority: {parsed['priority']}")
    if parsed["unread"]:
        bits.append("unread only")
    if parsed["important"]:
        bits.append("important only")
    if parsed["tokens"]:
        bits.append("text: " + " ".join(parsed["tokens"]))
    return " | ".join(bits)


def matches(email, cls, parsed: dict) -> bool:
    text = f"{email.sender_name} {email.sender_email} {email.subject} {email.body}"
    low = text.lower()
    if parsed["unread"] and email.is_read:
        return False
    if parsed["priority"] and (not cls or cls.priority != parsed["priority"]):
        return False
    if parsed["important"] and not (cls and cls.is_important):
        return False
    if parsed["from_text"] and parsed["from_text"] not in f"{email.sender_name} {email.sender_email}".lower():
        return False
    if parsed["categories"]:
        cats = {email.category} | ({cls.category} if cls else set())
        if not cats & set(parsed["categories"]):
            return False
    if any(not keyword_hit(k, text) for k in parsed["keywords"]):
        return False
    stemmed = " ".join(_stem(w) for w in re.findall(r"[a-z0-9][a-z0-9.\-/']*", low))
    return all(t in stemmed for t in parsed["tokens"])
