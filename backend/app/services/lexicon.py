"""Shared vocabulary: categories, profile presets, keyword topics and alias matching."""
import re

CATEGORIES = [
    "College Notification", "Examination Update", "Placement", "Job Opportunity",
    "Internship", "Interview Invitation", "Assessment", "Offer Letter",
    "Coding Competition", "Business Proposal", "Client Enquiry", "Invoice",
    "Meeting", "Project Update", "HR / Office", "Bank", "Shopping Promotion",
    "Newsletter", "Personal", "Social Media",
]

# Content signals used to infer an email's category from its text (not from the dataset label).
CATEGORY_SIGNALS = {
    "College Notification": ["college", "semester", "academic calendar", "registrar", "library",
                             "annual day", "department", "hod", "portal", "students", "campus"],
    "Examination Update": ["examination", "exam", "hall ticket", "revaluation", "timetable",
                           "mark sheet", "controller of examinations", "invigilat"],
    "Placement": ["placement", "campus drive", "pre-placement", "recruitment drive", "placement cell",
                  "cgpa", "2027 batch", "on-campus", "resume verification", "verified resume"],
    "Job Opportunity": ["is hiring", "hiring", "vacancy", "open position", "opening for", "ctc",
                        "lpa", "responsibilities", "years of experience", "apply before", "careers page",
                        "send your resume", "send your cv"],
    "Internship": ["intern", "internship", "stipend"],
    "Interview Invitation": ["interview", "shortlisted", "panel", "round 2", "google meet"],
    "Assessment": ["online assessment", "assessment link", "aptitude", "attempted once", "test has"],
    "Offer Letter": ["offer letter", "offer of employment", "pleased to offer", "delighted to offer",
                     "joining date", "annual ctc"],
    "Coding Competition": ["coding competition", "hackathon", "contest", "codesprint", "competitive",
                           "algorithmic problems", "rating changes"],
    "Business Proposal": ["proposal", "partnership", "reseller", "margin", "business development"],
    "Client Enquiry": ["enquiry", "inquiry", "quotation", "bulk", "demo", "pricing", "our team",
                       "request for quotation", "vendor"],
    "Invoice": ["invoice", "inv-", "payment is due", "receipt", "payment received", "amount due"],
    "Meeting": ["meeting", "calendar invite", "conference room", "client call", "dial-in", "agenda"],
    "Project Update": ["sprint", "blocker", "module", "release", "tickets", "status"],
    "HR / Office": ["timesheet", "health insurance", "employees", "hr operations", "payroll", "enrollment"],
    "Bank": ["debit card", "credit card", "debit alert", "otp", "bank", "statement", "minimum amount due"],
    "Shopping Promotion": ["sale", "% off", "discount", "coupon", "use code", "free delivery", "cart", "checkout"],
    "Newsletter": ["newsletter", "this week", "weekly", "digest", "read the full stories", "survey"],
    "Personal": ["amma", "family", "lunch", "photos", "take care", "trip"],
    "Social Media": ["viewed your profile", "followers", "following you", "liked your", "notifications",
                     "connection suggestions", "commented on"],
}

# What the chatbot understands as category mentions (regex -> category).
CATEGORY_ALIASES = [
    (r"\bcollege\b|\bcampus (news|notice)|\bacademic", "College Notification"),
    (r"\bexams?\b|\bexamination|\bhall tickets?|\bresults?\b", "Examination Update"),
    (r"\bplacements?\b|\bcampus (drives?|recruitment)|\bfresher recruitment", "Placement"),
    (r"\bjobs?\b|\brecruitment|\bhiring|\bvacanc|\bcareers?\b|\bopportunit|\bopenings?", "Job Opportunity"),
    (r"\binterns?\b|\binternships?", "Internship"),
    (r"\binterviews?", "Interview Invitation"),
    (r"\bassessments?|\bonline tests?|\btest links?|\bcoding tests?", "Assessment"),
    (r"\boffer letters?|\bjob offers?", "Offer Letter"),
    (r"\bcoding (competitions?|contests?|challenges?)|\bhackathons?|\bcontests?|\btechnical events?|\btech events?|\bcompetitive programming",
     "Coding Competition"),
    (r"\bbusiness proposals?|\bproposals?|\bpartnerships?", "Business Proposal"),
    (r"\bclients?\b|\bcustomers?\b|\ben?quir|\binquir|\bquotations?", "Client Enquiry"),
    (r"\binvoices?|\bbilling|\bpayment dues?", "Invoice"),
    (r"\bmeetings?|\bcalendar invites?|\bclient calls?", "Meeting"),
    (r"\bproject (updates?|status)|\bsprints?|\bstatus updates?", "Project Update"),
    (r"\bhr\b|\boffice (communications?|emails?|mails?)|\bwork communications?|\bworkplace|\boffice\b", "HR / Office"),
    (r"\bbank|\btransactions?|\bcredit cards?|\bdebit", "Bank"),
    (r"\bshopping|\bpromotions?|\boffers\b|\bsales?\b|\bdeals?\b|\bdiscounts?", "Shopping Promotion"),
    (r"\bnewsletters?|\bdigests?", "Newsletter"),
    (r"\bpersonal|\bfamily|\bfriends?\b", "Personal"),
    (r"\bsocial( media)?\b|\bsocial networks?", "Social Media"),
]

JOB_ROLE_CATEGORIES = {"Job Opportunity", "Internship"}

# Topic keywords: canonical name -> regexes searched in email text.
KEYWORD_TOPICS = {
    "data engineering": [r"data engineer", r"\betl\b", r"data pipeline", r"\bspark\b", r"airflow", r"lakehouse", r"data warehouse"],
    "python": [r"\bpython\b", r"\bfastapi\b", r"\bdjango\b"],
    "ai/ml": [r"\bml\b", r"machine learning", r"\bai\b", r"deep learning", r"\bnlp\b", r"\bllm\b", r"language model", r"pytorch", r"ai/ml"],
    "data science": [r"data scien", r"data analy", r"statistics"],
    "java": [r"\bjava\b", r"spring boot"],
    "frontend": [r"frontend", r"front-end", r"\breact\b", r"typescript"],
    "backend": [r"backend", r"back-end", r"\bapis?\b", r"microservices"],
    "cloud/devops": [r"\bcloud\b", r"devops", r"kubernetes", r"\baws\b", r"docker"],
    "cybersecurity": [r"cyber", r"security engineer", r"infosec"],
    "sales": [r"\bsales\b", r"distributors?"],
    "marketing": [r"marketing", r"\bseo\b", r"brand"],
}
KEYWORD_ALIASES = [
    (r"data engineer(ing|s)?", "data engineering"),
    (r"python( developer| dev)?", "python"),
    (r"\bai\s*/\s*ml\b|\bai and ml\b|machine learning|\bml\b|\bartificial intelligence\b|\bdeep learning\b|\bnlp\b|\bai\b", "ai/ml"),
    (r"data scien(ce|tist)|data analy(st|tics)", "data science"),
    (r"\bjava( developer)?\b", "java"),
    (r"front[- ]?end|\breact\b", "frontend"),
    (r"back[- ]?end", "backend"),
    (r"\bcloud\b|devops|\baws\b", "cloud/devops"),
    (r"cyber ?security|infosec", "cybersecurity"),
    (r"\bsales\b", "sales"),
    (r"marketing", "marketing"),
]

PROFILE_PRESETS = {
    "student": {
        "profession": "Student",
        "categories": ["College Notification", "Examination Update", "Placement", "Job Opportunity",
                       "Internship", "Interview Invitation", "Coding Competition"],
        "followups": ["Coding Competition", "Assessment"],
    },
    "businessperson": {
        "profession": "Businessperson",
        "categories": ["Business Proposal", "Client Enquiry", "Invoice", "Meeting"],
        "followups": ["Meeting", "Invoice"],
    },
    "job_seeker": {
        "profession": "Job Seeker",
        "categories": ["Job Opportunity", "Placement", "Interview Invitation", "Assessment", "Offer Letter"],
        "followups": ["Assessment", "Offer Letter", "Internship"],
    },
    "professional": {
        "profession": "Working Professional",
        "categories": ["HR / Office", "Project Update", "Meeting", "Client Enquiry"],
        "followups": ["Meeting", "Client Enquiry"],
    },
    "custom": {"profession": "", "categories": [], "followups": []},
}

FOLLOWUP_PHRASES = {
    "Coding Competition": "coding competitions and technical events",
    "Assessment": "online assessment links",
    "Meeting": "meeting notifications",
    "Invoice": "invoices",
    "Offer Letter": "offer letters",
    "Internship": "internship opportunities",
    "Client Enquiry": "client enquiries",
}


def find_categories(text: str) -> list[str]:
    text = text.lower()
    out = []
    for pattern, cat in CATEGORY_ALIASES:
        if re.search(pattern, text) and cat not in out:
            out.append(cat)
    return out


def find_keywords(text: str) -> list[str]:
    text = text.lower()
    out = []
    for pattern, kw in KEYWORD_ALIASES:
        if re.search(pattern, text) and kw not in out:
            out.append(kw)
    return out


def keyword_hit(keyword: str, text: str) -> bool:
    text = text.lower()
    patterns = KEYWORD_TOPICS.get(keyword.lower())
    if patterns is None:  # free-form keyword from the user / Gemini
        return keyword.lower() in text
    return any(re.search(p, text) for p in patterns)


def join_list(items: list[str]) -> str:
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]
