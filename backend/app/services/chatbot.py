"""Conversational preference engine.

Two interchangeable "understanding" back-ends return the same structure (an NLU dict):
  * Gemini (when configured and reachable)
  * a rule-based parser (always available)
Everything after understanding (state machine, preference updates, reclassification, replies)
is deterministic code, so behaviour is identical and testable in demo mode.
"""
import re

from sqlalchemy.orm import Session

from app.models import ChatMessage, Email, EmailClassification, UserPreference, UserProfile
from app.services import classifier, gemini, search, state
from app.services.lexicon import (CATEGORIES, FOLLOWUP_PHRASES, KEYWORD_TOPICS, PROFILE_PRESETS,
                                  find_categories, find_keywords, join_list)

YES = re.compile(r"^\s*(yes|yeah|yep|yup|sure|ok|okay|please do|please|definitely|of course|go ahead|y|include (them|it)|sounds good|why not)\b", re.I)
NO = re.compile(r"^\s*(no|nope|nah|not now|no thanks|no thank you|don'?t|do not|skip|n)\b", re.I)
NEGATION = re.compile(
    r"\b(stop (?:prioriti[sz]ing|showing|showing me)|don'?t (?:show|want|need|care about)|do not (?:show|want|need)|"
    r"exclude|ignore|remove|hide|not interested in|no more|without|skip|stop)\b", re.I)
INTEREST_CUES = re.compile(r"\b(emails?|mails?|notifications?|need|want|important|prioriti[sz]e|interested|show|include)\b", re.I)


def empty_nlu() -> dict:
    return {"intent": "other", "profession": None, "profession_key": None, "add_categories": [],
            "only_categories": [], "remove_categories": [], "boost_categories": [], "keywords_add": [],
            "keywords_remove": [], "search_query": None, "reply": None, "use_default": False}


# ------------------------------------------------------------------ rule-based NLU
def detect_profession(text: str, allow_custom: bool = False):
    low = text.lower()
    rules = [
        ("businessperson", "Businessperson", r"business ?(man|woman|person|owner)|entrepreneur|\bfounder\b|run(ning)? (a|my|our) (own )?(business|company|shop|startup)|self[- ]employed|shop owner"),
        ("job_seeker", "Job Seeker", r"job ?seeker|looking for (a |an )?(job|work|opportunit)|searching for (a |an )?(job|work)|unemployed|between jobs|preparing for [^.]*\bjobs?\b|fresh graduate"),
        ("student", "Student", r"\bstudent\b|undergrad|pursuing (my |a )?(b\.?tech|degree|b\.?e\b|m\.?tech|mba|bsc|msc)"),
        ("professional", "Working Professional", r"working professional|software engineer|\bdeveloper\b|\bmanager\b|\bemployee\b|consultant|\banalyst\b|\bdesigner\b|\bteacher\b|\bdoctor\b|\blawyer\b|work(ing)? (at|for|as|in)\b|corporate"),
    ]
    for key, label, pat in rules:
        if re.search(pat, low):
            return key, label
    if allow_custom:
        m = re.search(r"\bi(?:'m| am)(?: currently)?(?: a| an)? ([a-z][a-z \-/]{2,40}?)(?:[.,!]| and | who | working| at |$)", low)
        if m and not re.match(r"(preparing|looking|interested|planning|trying|going|not sure)", m.group(1)):
            return "custom", m.group(1).strip().title()
    return None, None


def rules_nlu(text: str, stage: str) -> dict:
    nlu = empty_nlu()
    low = text.lower().strip()
    if re.search(r"\b(reset|clear)\b.*\b(preferences|settings|everything)\b", low):
        nlu["intent"] = "reset"
        return nlu
    if re.match(r"^(help|what can you do|how (do|can) (i|you))\b", low):
        nlu["intent"] = "help"
        return nlu
    if re.match(r"^\s*(please )?(find|search( for)?|look for|locate|where (is|are)|do i have)\b", low):
        nlu["intent"] = "search"
        nlu["search_query"] = re.sub(r"^\s*(please )?(find( me)?|search( for)?|look for|locate|where (is|are)|do i have)\s*", "", low)
        return nlu
    if stage == "ask_interests" and re.search(r"not sure|default|usual|standard|whatever|everything relevant", low):
        nlu["intent"], nlu["use_default"] = "update", True
        return nlu

    pkey, plabel = detect_profession(text, allow_custom=(stage == "ask_profession"))
    nlu["profession_key"], nlu["profession"] = pkey, plabel

    m = NEGATION.search(low)
    if m:
        tail = re.split(r"\bbut\b|\binstead\b|;|\.", low[m.end():], maxsplit=1)
        neg_part = tail[0]
        pos_part = low[:m.start()] + " " + (tail[1] if len(tail) > 1 else "")
    else:
        neg_part, pos_part = "", low

    pos_cats = find_categories(pos_part)
    if stage == "ask_profession" and not INTEREST_CUES.search(pos_part):
        pos_cats = []  # "final-year college student" must not select College Notification
    nlu["remove_categories"] = find_categories(neg_part)
    nlu["keywords_remove"] = find_keywords(neg_part)
    nlu["keywords_add"] = find_keywords(pos_part)
    if re.search(r"\b(only|just)\b", pos_part) and pos_cats:
        nlu["only_categories"] = pos_cats
    elif re.search(r"\b(prioriti[sz]e|focus on|boost|most important)\b", pos_part):
        nlu["boost_categories"] = pos_cats
        nlu["add_categories"] = pos_cats
    else:
        nlu["add_categories"] = pos_cats
    has_change = any(nlu[k] for k in ("add_categories", "only_categories", "remove_categories",
                                       "keywords_add", "keywords_remove", "boost_categories"))
    if has_change:
        nlu["intent"] = "update"
    elif pkey or (stage == "ask_profession" and 0 < len(low.split()) <= 5 and not re.match(r"^(hi|hello|hey)\b", low)):
        nlu["intent"] = "profession"
        if not pkey:
            nlu["profession"], nlu["profession_key"] = text.strip().title(), "custom"
    elif re.match(r"^(hi|hello|hey|good (morning|evening|afternoon))\b", low):
        nlu["intent"] = "greeting"
    return nlu


# ------------------------------------------------------------------ Gemini NLU
NLU_SYSTEM = ("You extract email-preference changes from a user's chat message for an email triage assistant. "
              "Respond with JSON only.")


def gemini_nlu(text: str, stage: str, pref: UserPreference, history: list[str]) -> dict:
    prompt = (
        f"Conversation stage: {stage} (ask_profession = we just asked their profession; ask_interests = we asked "
        f"what emails matter).\nCurrent preferences: categories={pref.categories}, boosted={pref.boosted_categories}, "
        f"excluded={pref.excluded_categories}, keywords={pref.keywords}, profession={pref.profession!r}\n"
        f"Recent chat:\n" + "\n".join(history[-6:]) + f"\n\nNEW USER MESSAGE: {text!r}\n\n"
        f"ALLOWED CATEGORIES: {CATEGORIES}\n"
        f"KNOWN KEYWORD TOPICS: {list(KEYWORD_TOPICS)} (free-form keywords such as job roles or skills are allowed too)\n\n"
        "Return a JSON object with keys:\n"
        "intent: one of update | search | profession | reset | help | greeting | other\n"
        "profession: string or null (the user's profession, e.g. 'Final-year student')\n"
        "profession_key: one of student | businessperson | job_seeker | professional | custom | null\n"
        "add_categories, only_categories, remove_categories, boost_categories: arrays of ALLOWED CATEGORIES\n"
        "  (only_categories means 'show only these'; at ask_profession stage do NOT infer categories from the profession alone)\n"
        "keywords_add, keywords_remove: arrays of short lowercase strings (roles, skills, topics)\n"
        "search_query: string or null (for 'find ...' requests, the search phrase)\n"
        "use_default: true only if the user says they are not sure and want typical defaults\n"
        "reply: a short friendly answer ONLY when intent is 'other'; otherwise null")
    data = gemini.generate_json(prompt, system=NLU_SYSTEM)
    if isinstance(data, list) and data:
        data = data[0]
    nlu = empty_nlu()
    if not isinstance(data, dict):
        raise gemini.GeminiError("Gemini returned an unexpected NLU format")
    nlu["intent"] = data.get("intent") if data.get("intent") in {"update", "search", "profession", "reset", "help", "greeting", "other"} else "other"
    for k in ("add_categories", "only_categories", "remove_categories", "boost_categories"):
        nlu[k] = [c for c in (data.get(k) or []) if c in CATEGORIES]
    for k in ("keywords_add", "keywords_remove"):
        nlu[k] = [str(x).lower().strip() for x in (data.get(k) or []) if str(x).strip()][:6]
    nlu["profession"] = (data.get("profession") or None)
    pk = data.get("profession_key")
    nlu["profession_key"] = pk if pk in PROFILE_PRESETS else ("custom" if nlu["profession"] else None)
    nlu["search_query"] = data.get("search_query") or None
    nlu["reply"] = data.get("reply") or None
    nlu["use_default"] = bool(data.get("use_default"))
    return nlu


# ------------------------------------------------------------------ applying changes
def _uniq(seq):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


def apply_nlu(pref: UserPreference, nlu: dict) -> list[str]:
    """Mutate preferences; return human-readable change notes (empty if nothing changed)."""
    notes: list[str] = []
    cats, boosted, excluded, kws = (list(pref.categories or []), list(pref.boosted_categories or []),
                                    list(pref.excluded_categories or []), list(pref.keywords or []))
    if nlu["only_categories"]:
        cats = list(nlu["only_categories"])
        boosted = [b for b in boosted if b in cats]
        excluded = [x for x in excluded if x not in cats]
        notes.append(f"showing only {join_list(cats)}")
    added = [c for c in _uniq(nlu["add_categories"] + nlu["boost_categories"]) if c not in cats]
    if added:
        cats += added
        notes.append(f"added {join_list(added)}")
    for c in nlu["add_categories"] + nlu["boost_categories"]:
        if c in excluded:
            excluded.remove(c)
    new_boost = [c for c in nlu["boost_categories"] if c not in boosted]
    if new_boost:
        boosted += new_boost
        notes.append(f"boosted {join_list(new_boost)}")
    removed = [c for c in nlu["remove_categories"]]
    if removed:
        cats = [c for c in cats if c not in removed]
        boosted = [c for c in boosted if c not in removed]
        excluded = _uniq(excluded + removed)
        notes.append(f"stopped prioritizing {join_list(removed)}")
    new_kw = [k for k in nlu["keywords_add"] if k not in kws]
    if new_kw:
        kws += new_kw
        notes.append(f"now following {join_list([k.title() for k in new_kw])}")
    gone_kw = [k for k in nlu["keywords_remove"] if k in kws]
    if gone_kw:
        kws = [k for k in kws if k not in gone_kw]
        notes.append(f"no longer following {join_list([k.title() for k in gone_kw])}")
    pref.categories, pref.boosted_categories, pref.excluded_categories, pref.keywords = cats, boosted, excluded, kws
    return notes


def _followup_for_onboarding(pref: UserPreference, pkey: str | None):
    for cand in PROFILE_PRESETS.get(pkey or "custom", {}).get("followups", []):
        if cand not in (pref.categories or []):
            return cand
    return None


def _counts(db: Session, profile: UserProfile) -> tuple[int, int]:
    total = db.query(Email).count()
    imp = db.query(EmailClassification).filter_by(profile_id=profile.id, is_important=True).count()
    return imp, total


def _reclassify(db: Session, profile: UserProfile, pref: UserPreference) -> dict:
    pref.version = (pref.version or 0) + 1
    db.commit()
    return classifier.classify_all(db, profile, "auto")


HELP = ("I can learn what matters to you and re-rank the same inbox. Try: \"Show only college emails\", "
        "\"Prioritize placement notifications\", \"Include internships\", \"Show Data Engineering jobs\", "
        "\"Stop prioritizing shopping emails\", \"Show business proposals\" or \"Find interview invitations\".")


def handle_message(db: Session, profile: UserProfile, text: str) -> dict:
    conv = state.get_conversation(db, profile)
    pref = state.get_pref(db, profile)
    st = dict(conv.state or {})
    stage, pending = st.get("stage", "ready"), st.get("pending")
    history = [f"{m.role}: {m.content}" for m in
               db.query(ChatMessage).filter_by(conversation_id=conv.id).order_by(ChatMessage.id.desc()).limit(8)][::-1]
    db.add(ChatMessage(conversation_id=conv.id, role="user", content=text))
    db.commit()

    result = {"reply": "", "engine": "rules", "classification": None, "preferences_changed": False,
              "action": None, "ai_error": None}
    reply_parts: list[str] = []

    def finish(extra_state: dict | None = None):
        st.update(extra_state or {})
        conv.state = st
        reply = " ".join(p for p in reply_parts if p).strip()
        db.add(ChatMessage(conversation_id=conv.id, role="assistant", content=reply, engine=result["engine"]))
        db.commit()
        result["reply"] = reply
        return result

    def changed(notes_text: str | None = None):
        info = _reclassify(db, profile, pref)
        result["classification"] = info
        result["preferences_changed"] = True
        if info.get("error"):
            result["ai_error"] = info["error"]
        imp, total = _counts(db, profile)
        state.log_activity(db, profile.id, "preferences", notes_text or "Preferences updated")
        db.commit()
        return imp, total

    # 1) answer to a pending yes/no question -------------------------------------------------
    if pending and (YES.match(text) or NO.match(text)) and len(text.split()) <= 6 and not find_categories(text):
        if YES.match(text):
            nlu = empty_nlu()
            nlu["add_categories"] = pending.get("categories", [])
            nlu["keywords_add"] = pending.get("keywords", [])
            notes = apply_nlu(pref, nlu)
            pref.onboarded = True
            imp, total = changed("Added " + join_list(pending.get("categories", [])))
            if stage in ("ask_followup", "ask_interests", "ask_profession"):
                reply_parts.append("Perfect! I have understood your requirements. I will prioritize these emails for you.")
            else:
                reply_parts.append("Your preferences have been updated.")
            reply_parts.append(f"{imp} of {total} emails are now in your Priority Inbox.")
        else:
            reply_parts.append("No problem, I'll leave that out." +
                               (" I have understood your requirements and will prioritize these emails for you."
                                if stage == "ask_followup" else ""))
            pref.onboarded = True
            db.commit()
            if stage == "ask_followup" and not pref.classified_at:
                changed("Onboarding finished")
        return finish({"stage": "ready", "pending": None})

    # 2) understand the message --------------------------------------------------------------
    nlu, engine = None, "rules"
    if gemini.is_available():
        try:
            nlu, engine = gemini_nlu(text, stage, pref, history), "gemini"
        except gemini.GeminiError as exc:
            result["ai_error"] = f"Gemini failed ({exc}); used the built-in rule-based understanding instead."
    elif gemini.is_configured():
        result["ai_error"] = f"Gemini temporarily skipped after a recent failure: {gemini.last_error}"
    if nlu is None:
        nlu = rules_nlu(text, stage)
    result["engine"] = engine
    # a stale pending question is dropped when the user says something else
    st["pending"] = None

    intent = nlu["intent"]
    if nlu["profession"]:
        pref.profession = nlu["profession"]
        st["profession_key"] = nlu["profession_key"]
        db.commit()

    # global intents
    if intent == "help":
        reply_parts.append(HELP)
        return finish()
    if intent == "reset":
        state.apply_preset(db, profile, pref)
        imp, total = changed("Preferences reset to profile defaults")
        reply_parts.append(f"I've reset your preferences to the {profile.name} defaults. {imp} of {total} emails are in your Priority Inbox.")
        return finish({"stage": "ready"})
    if intent == "search":
        q = nlu["search_query"] or text
        parsed = search.parse_query(q)
        emails = db.query(Email).all()
        cls = {c.email_id: c for c in db.query(EmailClassification).filter_by(profile_id=profile.id)}
        n = sum(1 for e in emails if search.matches(e, cls.get(e.id), parsed))
        result["action"] = {"type": "search", "query": q, "count": n}
        state.log_activity(db, profile.id, "search", f"Searched for \"{q}\"")
        reply_parts.append(f"I found {n} email{'s' if n != 1 else ''} matching \"{q}\" in All Inbox. Opening the results now." if n
                           else f"I couldn't find any emails matching \"{q}\". Nothing was deleted; try different words.")
        db.commit()
        return finish()

    # 3) onboarding state machine ------------------------------------------------------------
    if stage == "ask_profession":
        if intent == "update":  # profession + interests given in one message
            apply_nlu(pref, nlu)
            return _after_interests(db, profile, pref, st, reply_parts, changed, finish, nlu)
        if nlu["profession"]:
            reply_parts.append("Great! What kind of emails are important to you?")
            return finish({"stage": "ask_interests"})
        reply_parts.append("What is your profession? For example: student, business owner, job seeker or software engineer.")
        return finish()

    if stage == "ask_interests":
        if nlu["use_default"]:
            preset = PROFILE_PRESETS.get(st.get("profession_key") or "custom")
            if preset and preset["categories"]:
                nlu["add_categories"] = list(preset["categories"])
                apply_nlu(pref, nlu)
                return _after_interests(db, profile, pref, st, reply_parts, changed, finish, nlu)
        if intent == "update":
            apply_nlu(pref, nlu)
            return _after_interests(db, profile, pref, st, reply_parts, changed, finish, nlu)
        reply_parts.append("I couldn't match that to the topics I know. Try naming things like college notifications, "
                           "placements, internships, job opportunities, client enquiries, invoices or meetings.")
        return finish()

    # 4) normal (ready) mode -----------------------------------------------------------------
    if intent == "update":
        notes = apply_nlu(pref, nlu)
        if not notes:
            reply_parts.append("Those preferences were already set, so nothing changed.")
            return finish({"stage": "ready"})
        pref.onboarded = True
        imp, total = changed("Updated: " + "; ".join(notes))
        reply_parts.append(f"Your preferences have been updated: {'; '.join(notes)}.")
        reply_parts.append(f"{imp} of {total} emails are now in your Priority Inbox, and all {total} stay available in All Inbox.")
        followup = None
        if (nlu["keywords_add"] and "Job Opportunity" in (pref.categories or [])
                and not {"Internship", "Placement"} <= set(pref.categories or [])):
            missing = [c for c in ("Internship", "Placement") if c not in (pref.categories or [])]
            followup = {"categories": missing,
                        "question": "Should I include internships and fresher recruitment notifications?"}
        if followup:
            reply_parts.append(followup["question"])
            return finish({"stage": "ready", "pending": {"categories": followup["categories"]}})
        return finish({"stage": "ready"})
    if intent == "profession":
        reply_parts.append(f"Got it, I've noted that you're a {pref.profession}. Tell me which emails matter most and I'll re-rank your inbox.")
        return finish()
    if intent == "greeting":
        reply_parts.append("Hi! Tell me what kind of emails matter to you right now and I'll update your Priority Inbox.")
        return finish()
    reply_parts.append(nlu["reply"] or ("I wasn't sure what to change. " + HELP))
    return finish()


def _after_interests(db, profile, pref, st, reply_parts, changed, finish, nlu):
    pref.onboarded = True
    imp, total = changed("Onboarding: " + join_list(pref.categories or []))
    cand = _followup_for_onboarding(pref, st.get("profession_key"))
    if cand:
        reply_parts.append(f"Would you also like {FOLLOWUP_PHRASES.get(cand, cand.lower())}?")
        return finish({"stage": "ask_followup", "pending": {"categories": [cand]}})
    reply_parts.append("Perfect! I have understood your requirements. I will prioritize these emails for you.")
    reply_parts.append(f"{imp} of {total} emails are in your Priority Inbox.")
    return finish({"stage": "ready", "pending": None})
