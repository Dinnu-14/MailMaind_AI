"""Email summaries. Gemini when available; otherwise extractive (only text found in the email)."""
import json
import re

from sqlalchemy.orm import Session

from app.models import Email
from app.services import gemini

GREETING_RE = re.compile(r"^(dear|hi|hello|hey|greetings)\b[^.]{0,60}[,:!]?$", re.I)
DATE_RE = re.compile(
    r"(?:(?:before|by|until|on|from|due|expires on|close on|closes on|starts)\s+)?"
    r"(?:(?:Nov(?:ember)?|Dec(?:ember)?|Jan(?:uary)?|Mar(?:ch)?)\s+\d{1,2}(?:\s*[-\u2013]\s*\d{1,2})?"
    r"(?:\s+at\s+\d{1,2}(?::\d{2})?\s*[AP]M)?|(?:by|before|until)\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Sunday)"
    r"|tomorrow(?:\s+at\s+\d{1,2}(?::\d{2})?\s*[AP]M)?|tonight(?:\s+at\s+\w+)?|Tuesday at \d{1,2}:\d{2} [AP]M"
    r"|within \d+ (?:working )?(?:days|hours))", re.I)
ACTION_RE = re.compile(
    r"\b(please|kindly|must|register|submit|confirm|reply|apply|pay|sign|return|upload|send|accept|"
    r"complete|update|block|download|add your|share)\b", re.I)
REQUEST_RE = re.compile(r"\b(could you|can you|would you|would like|we would|invite you|interested in|requested|please|kindly)\b", re.I)
INFO_RE = re.compile(r"(\d|rs\.|\u20b9|lpa|cgpa|stipend|prize|%)", re.I)


def _sentences(body: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", body)
    out = []
    for s in (p.strip() for p in parts):
        if len(s) < 4 or GREETING_RE.match(s) or re.match(r"^(regards|best regards|thanks|thank you)[,.]?$", s, re.I):
            continue
        out.append(s)
    return out


def rule_summary(e: Email) -> dict:
    sents = _sentences(e.body)
    body_sents = [s for s in sents if not re.match(r"^(regards|best|hr team|office of|placement cell|controller)", s, re.I)]
    purpose = body_sents[0] if body_sents else e.subject
    deadlines = []
    for m in DATE_RE.finditer(e.body):
        t = m.group(0).strip()
        if t and t.lower() not in [d.lower() for d in deadlines] and re.search(r"\d|tomorrow|tonight|friday|thursday|tuesday|sunday|monday|wednesday", t, re.I):
            deadlines.append(t)
    info = [s for s in body_sents[1:] if INFO_RE.search(s)][:3]
    actions = [s for s in body_sents if ACTION_RE.search(s) and s != purpose][:2]
    if not actions and re.search(r"no (further )?action", e.body, re.I):
        actions = ["No action required."]
    requests = [s for s in body_sents if REQUEST_RE.search(s)][:1]
    return {
        "purpose": purpose,
        "important_information": info or ([body_sents[1]] if len(body_sents) > 1 else []),
        "deadlines": deadlines[:5],
        "required_action": " ".join(actions) if actions else "None mentioned in the email.",
        "sender_request": requests[0] if requests else "None mentioned in the email.",
    }


GEMINI_SYSTEM = ("You summarize emails faithfully. Use ONLY facts stated in the email. If something is not "
                 "mentioned write 'None mentioned in the email.' Respond with JSON only.")


def gemini_summary(e: Email) -> dict:
    prompt = (
        "Summarize this email as JSON with keys: purpose (string), important_information (array of short "
        "strings), deadlines (array of strings copied from the email), required_action (string), "
        "sender_request (string).\n\n"
        f"From: {e.sender_name} <{e.sender_email}>\nSubject: {e.subject}\nDate: {e.date}\n\n{e.body}")
    data = gemini.generate_json(prompt, system=GEMINI_SYSTEM)
    if isinstance(data, list) and data:
        data = data[0]
    for k in ("purpose", "important_information", "deadlines", "required_action", "sender_request"):
        if k not in data:
            raise gemini.GeminiError(f"Gemini summary missing field '{k}'")
    data["important_information"] = [str(x) for x in data["important_information"]][:5]
    data["deadlines"] = [str(x) for x in data["deadlines"]][:5]
    return data


def get_summary(db: Session, e: Email) -> tuple[dict, str]:
    if e.summary_json and (e.summary_engine == "gemini" or not gemini.is_available()):
        return json.loads(e.summary_json), e.summary_engine or "rules"
    engine, data = "rules", None
    if gemini.is_available():
        try:
            data, engine = gemini_summary(e), "gemini"
        except gemini.GeminiError:
            data = None
    if data is None:
        data = rule_summary(e)
    e.summary_json, e.summary_engine = json.dumps(data), engine
    db.commit()
    return data, engine
