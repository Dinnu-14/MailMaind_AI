"""End-to-end API tests (demo mode, no Gemini key). Run: pytest -q"""
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["GEMINI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def switch(client, key, reset=True):
    r = client.post("/api/profiles/switch", json={"key": key, "reset_conversation": reset})
    assert r.status_code == 200
    return r.json()


def priority_ids(client):
    return {e["id"] for e in client.get("/api/emails/priority").json()["items"]}


def cats(client, ids):
    items = {e["id"]: e for e in client.get("/api/emails").json()["items"]}
    return {items[i]["classification"]["category"] for i in ids}


def test_health(client):
    d = client.get("/api/health").json()
    assert d["status"] == "ok" and d["gemini_configured"] is False


def test_dataset_size_and_nothing_deleted(client):
    items = client.get("/api/emails").json()["items"]
    assert len(items) >= 30
    for key in ("student", "businessperson", "job_seeker", "professional"):
        switch(client, key)
        assert client.get("/api/emails").json()["total"] == len(items)


def test_same_emails_different_results_per_profile(client):
    switch(client, "student")
    s = priority_ids(client)
    s_cats = cats(client, s)
    switch(client, "businessperson")
    b = priority_ids(client)
    b_cats = cats(client, b)
    assert s and b and s != b
    assert "Placement" in s_cats and "Placement" not in b_cats
    assert {"Business Proposal", "Client Enquiry", "Invoice"} & b_cats
    assert not ({"Business Proposal", "Invoice"} & s_cats)
    assert "Shopping Promotion" not in s_cats | b_cats


def test_classification_fields(client):
    switch(client, "student")
    for e in client.get("/api/emails").json()["items"]:
        c = e["classification"]
        assert c["priority"] in {"High", "Medium", "Low", "Other"}
        assert 0 <= c["relevance_score"] <= 100 and c["reason"]
        assert c["engine"] == "rules"
        assert c["is_important"] == (c["priority"] != "Other")


def test_email_detail_summary_and_read(client):
    switch(client, "student")
    first = client.get("/api/emails/priority").json()["items"][0]
    d = client.get(f"/api/emails/{first['id']}").json()
    assert d["body"] and d["summary"]["purpose"] and d["summary"]["engine"] == "rules"
    assert client.get(f"/api/emails/{first['id']}?mark_read=false").json()["is_read"] is True
    assert client.get("/api/emails/99999").status_code == 404


def test_filters_search_sort(client):
    switch(client, "student")
    all_ = client.get("/api/emails").json()
    ids = client.get("/api/emails?important=true").json()["total"]
    assert ids + client.get("/api/emails?important=false").json()["total"] == all_["total"]
    assert client.get("/api/emails?category=Invoice").json()["total"] >= 1
    assert client.get("/api/emails?priority=High").json()["total"] >= 1
    dates = [e["date"] for e in client.get("/api/emails?sort=date_desc").json()["items"]]
    assert dates == sorted(dates, reverse=True)
    r = client.get("/api/emails?q=hall ticket").json()
    assert r["total"] >= 1
    assert client.get("/api/emails?q=zzzqqqxyz").json()["total"] == 0
    assert client.get("/api/emails?q=from placement").json()["total"] >= 1
    assert client.get("/api/emails?category=Nope").status_code == 422


def test_chat_onboarding_flow(client):
    switch(client, "custom")
    hist = client.get("/api/chat/history").json()
    assert "profession" in hist[0]["content"].lower()
    r = client.post("/api/chat", json={"message": "I am a final-year college student."}).json()
    assert "important to you" in r["reply"]
    r = client.post("/api/chat", json={"message": "I mainly need college notifications, placements, internships, job opportunities and interview notifications."}).json()
    assert r["preferences_changed"] and "coding competitions" in r["reply"].lower()
    r = client.post("/api/chat", json={"message": "Yes"}).json()
    assert "understood your requirements" in r["reply"]
    p = client.get("/api/preferences").json()
    assert {"College Notification", "Placement", "Internship", "Job Opportunity",
            "Interview Invitation", "Coding Competition"} <= set(p["categories"])
    assert p["onboarded"] and "student" in p["profession"].lower()
    assert len(priority_ids(client)) > 0
    assert len(client.get("/api/chat/history").json()) >= 7


def test_chat_preference_changes(client):
    switch(client, "student")
    n0 = len(priority_ids(client))
    r = client.post("/api/chat", json={"message": "Show only college emails"}).json()
    assert r["preferences_changed"]
    ids = priority_ids(client)
    assert 0 < len(ids) < n0 and cats(client, ids) == {"College Notification"}
    assert client.get("/api/emails").json()["total"] >= 30
    client.post("/api/chat", json={"message": "Include internships"})
    assert "Internship" in client.get("/api/preferences").json()["categories"]
    client.post("/api/chat", json={"message": "Prioritize placement notifications"})
    p = client.get("/api/preferences").json()
    assert "Placement" in p["boosted_categories"]
    client.post("/api/chat", json={"message": "Stop prioritizing shopping emails"})
    assert "Shopping Promotion" in client.get("/api/preferences").json()["excluded_categories"]
    client.post("/api/chat", json={"message": "Show business proposals"})
    assert "Business Proposal" in cats(client, priority_ids(client))


def test_chat_data_engineering_followup(client):
    switch(client, "job_seeker")
    r = client.post("/api/chat", json={"message": "Now I am preparing for Data Engineering jobs. Show me Data Engineer, Python Developer and AI/ML opportunities."}).json()
    assert r["preferences_changed"]
    assert "internships and fresher" in r["reply"].lower()
    p = client.get("/api/preferences").json()
    assert {"data engineering", "python", "ai/ml"} <= set(p["keywords"])
    r = client.post("/api/chat", json={"message": "Yes"}).json()
    assert "updated" in r["reply"].lower()
    assert "Internship" in client.get("/api/preferences").json()["categories"]


def test_chat_find_and_validation(client):
    switch(client, "student")
    r = client.post("/api/chat", json={"message": "Find interview invitations"}).json()
    assert r["action"]["type"] == "search" and r["action"]["count"] >= 1
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={"message": "x" * 2000}).status_code == 422
    assert client.post("/api/chat", json={}).status_code == 422


def test_preferences_put_persist_and_validate(client):
    switch(client, "student")
    r = client.put("/api/preferences", json={"categories": ["Invoice", "Meeting"]})
    assert r.status_code == 200 and r.json()["categories"] == ["Invoice", "Meeting"]
    assert cats(client, priority_ids(client)) <= {"Invoice", "Meeting"}
    assert client.get("/api/preferences").json()["categories"] == ["Invoice", "Meeting"]
    assert client.put("/api/preferences", json={"categories": ["Bogus"]}).status_code == 422


def test_preferences_survive_profile_switch(client):
    switch(client, "student")
    client.put("/api/preferences", json={"categories": ["Bank"]})
    switch(client, "businessperson", reset=False)
    switch(client, "student", reset=False)
    assert client.get("/api/preferences").json()["categories"] == ["Bank"]


def test_classify_endpoint_and_gemini_honesty(client):
    switch(client, "student")
    d = client.post("/api/classify", json={"engine": "rules"}).json()
    assert d["engine"] == "rules" and len(d["results"]) == d["total"]
    assert client.post("/api/classify", json={}).json()["engine"] == "rules"
    r = client.post("/api/classify", json={"engine": "gemini"})
    assert r.status_code == 502 and "GEMINI_API_KEY" in r.json()["detail"]


def test_feedback_override(client):
    switch(client, "student")
    other = next(e for e in client.get("/api/emails?important=false").json()["items"])
    r = client.post("/api/feedback", json={"email_id": other["id"], "is_correct": False, "expected_important": True})
    assert r.status_code == 200
    assert other["id"] in priority_ids(client)
    assert client.post("/api/feedback", json={"email_id": other["id"], "is_correct": False}).status_code == 422
    assert client.post("/api/feedback", json={"email_id": 99999, "is_correct": True}).status_code == 404


def test_stats_profiles_reload(client):
    switch(client, "student")
    s = client.get("/api/dashboard/stats").json()
    assert s["total"] == s["important"] + s["other"] and s["recent_activity"]
    assert sum(s["by_priority"].values()) == s["total"]
    profs = client.get("/api/profiles").json()
    assert [p["key"] for p in profs] == ["student", "businessperson", "job_seeker", "professional", "custom"]
    assert sum(p["is_active"] for p in profs) == 1
    assert client.post("/api/profiles/switch", json={"key": "nope"}).status_code == 422
    assert client.post("/api/emails/reload").json()["loaded"] >= 30
    assert client.get("/api/dashboard/stats").json()["unread"] >= 1


def test_cors(client):
    r = client.options("/api/health", headers={"Origin": "http://localhost:5173",
                                                "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_concurrent_requests_do_not_race(client):
    """Regression: parallel requests on stale classifications used to violate the unique constraint."""
    from concurrent.futures import ThreadPoolExecutor
    switch(client, "student")
    client.put("/api/preferences", json={"categories": ["Placement"]})
    from app.database import SessionLocal
    from app.models import EmailClassification
    db = SessionLocal(); db.query(EmailClassification).delete(); db.commit(); db.close()
    urls = ["/api/dashboard/stats", "/api/emails/priority", "/api/emails", "/api/dashboard/stats"] * 3
    with ThreadPoolExecutor(8) as ex:
        codes = list(ex.map(lambda u: client.get(u).status_code, urls))
    assert codes == [200] * len(urls)
