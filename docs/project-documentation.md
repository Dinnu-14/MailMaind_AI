# Project documentation and demo guide

## Problem
Email importance is personal. A placement drive matters to a student and is noise to a shop owner. Fixed categories cannot capture that, so this project lets the user *describe* their needs in chat and ranks the same inbox accordingly.

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Status, Gemini configured or demo mode |
| GET | `/api/emails` | All emails. Filters: `q`, `category`, `priority`, `important`, `unread`, `sort` |
| GET | `/api/emails/priority` | Only important emails, same filters |
| GET | `/api/emails/{id}` | Full email, classification, summary (marks as read) |
| POST | `/api/emails/reload` | Sync: reload sample emails and reset read status |
| POST | `/api/chat` | Send a message; returns reply and whether preferences changed |
| GET / POST | `/api/chat/history`, `/api/chat/reset` | Conversation |
| GET / PUT | `/api/preferences` | Read or edit preferences (reclassifies on save) |
| POST | `/api/classify` | Reclassify with `auto`, `rules` or `gemini` |
| GET | `/api/dashboard/stats` | Counts, breakdowns, activity, engine |
| POST | `/api/feedback` | Mark a classification right or wrong |
| GET / POST | `/api/profiles`, `/api/profiles/switch` | Demo profiles |

Interactive docs: `http://localhost:8000/docs`.

## Sample data
`backend/data/sample_emails.json`: 44 emails over 20 categories (college, exams, placement, jobs, internships, interviews, assessments, offers, coding contests, proposals, client enquiries, invoices, meetings, project updates, HR, bank, shopping, newsletters, personal, social). Each has a full body, so classification and summaries use the content, not only the subject.

## Demo script (about 5 minutes)
1. **First open.** The app lands on the chatbot. Answer: *"I am a final-year college student."* Then *"I mainly need college notifications, placements, internships, job opportunities and interview notifications."* Then *"Yes"* to coding competitions. The Priority Inbox fills.
2. **Show the reasons.** Open Priority Inbox; point at the colored priority rail, score and the "Why" line on each email.
3. **Nothing is lost.** Open All Inbox: all 44 emails are there, including shopping, bank and business mail.
4. **Open an email.** Show the summary (purpose, deadlines, required action) and the explanation panel.
5. **Change your mind in chat.** Open **Ask AI** and type *"Now I am preparing for Data Engineering jobs. Show me Data Engineer, Python Developer and AI/ML opportunities."* Answer *"Yes"* to the internships follow-up. The inbox re-ranks immediately; non-matching jobs drop.
6. **Natural-language commands.** *"Show only college emails"*, *"Stop prioritizing shopping emails"*, *"Find interview invitations"* (opens search results).
7. **The key idea.** Use the profile switcher (top right) to go Student > Businessperson > Job Seeker. The *same 44 emails* produce different Priority Inboxes.
8. **Feedback.** On an email, click "This is important" and watch it move into the Priority Inbox.
9. **Honesty.** Mention the banner: without a Gemini key the local rule-based engine runs, and each result says which engine produced it. Add a key to switch to Gemini.

## Limitations
- Demo project: no real Gmail access or credentials, a single shared user, no authentication.
- The rule-based engine knows a fixed vocabulary of topics and job skills. Gemini handles open-ended wording better.
- The Gemini path needs a real key and network to exercise; it was not run during development, only its error handling was tested (forcing Gemini without a key returns a clear error).
