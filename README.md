# MindMate

MindMate is an experimental wellbeing journaling application that will combine journal entries and an AI voice conversation with privacy-aware text processing, emotion analysis, an explainable application-level mood estimate, and a seven-day dashboard.

It is not a medical device, diagnostic system, psychiatric assessment, or replacement for a qualified mental-health professional.

## Current status

Phases 1–14 are complete. The protected privacy-aware text pipeline performs
local language detection, local obvious-PII masking, Gemini translation of only
the redacted text, structured emotion classification, and an explainable mood
score. Multiple analyses are aggregated into deterministic UTC daily mood
records. The authenticated dashboard displays today's result, emotion
distribution, seven-day trend, and recent activity. The Gemini Live voice
assistant now streams microphone audio, spoken responses, and transcripts.
Completed transcripts can be explicitly saved, analyzed, and included in daily
mood records. Automated end-to-end contract testing and security verification
are in place. The final responsive UI includes shared authentication layouts,
desktop and mobile navigation, accessible focus states, reduced-motion support,
and polished loading, error, empty, and success states.

## Planned architecture

```text
React + Vite browser app
  |-- Firebase Authentication (email/password)
  |-- REST calls with Firebase ID token
  |-- Gemini Live connection using a short-lived token
  v
FastAPI application
  |-- verifies Firebase ID tokens
  |-- detects language and masks obvious PII
  |-- calls Gemini for translation and structured emotion scores
  |-- calculates explainable mood estimates
  |-- provisions short-lived Gemini Live tokens
  v
Cloud Firestore
  `-- users/{uid}/{journals|conversations|analyses|dailyMood}/{document}
```

The backend will remain one deployable service. Gemini and Firestore access will be wrapped in small service modules so they can be replaced without changing API routes.

## Non-functional requirements

MindMate's measurable security, privacy, performance, reliability,
accessibility, observability, maintainability, portability, and responsible-AI
requirements are defined in [NFRS.md](./NFRS.md). That document also separates
controls enforced by the current application from deployment targets that must
be validated in a production environment.

## Repository layout

```text
Mindmate/
|-- backend/
|   |-- app/
|   |   |-- models/
|   |   |-- routes/
|   |   |-- services/
|   |   `-- utils/
|   |-- tests/
|   `-- .env.example
|-- firebase/
|   `-- firestore.rules
|-- frontend/
|   |-- public/
|   |-- src/
|   |   |-- components/
|   |   |-- contexts/
|   |   |-- lib/
|   |   `-- pages/
|   `-- .env.example
|-- .gitignore
`-- README.md
```

## Local prerequisites

- Git 2.40 or newer
- Node.js 22 LTS (Vite currently requires Node.js 20.19+ or 22.12+)
- npm 10 or newer
- Python 3.11 or 3.12 recommended
- A modern Chromium-based browser with microphone permission

Python 3.13 may work, but Python 3.12 is the conservative choice for third-party package compatibility.

## Planned dependencies

### Frontend runtime

- `react`, `react-dom`
- `react-router-dom`
- `firebase`
- `@google/genai`
- `recharts`
- `lucide-react`

### Frontend development

- `vite`, `@vitejs/plugin-react`
- `tailwindcss`, `@tailwindcss/vite`
- ESLint and React ESLint plugins from the Vite template
- `vitest`

### Backend runtime

- `fastapi`, `uvicorn[standard]`
- `firebase-admin`
- `google-genai`
- `pydantic-settings`
- `langdetect`

### Backend development and testing

- `pytest`, `pytest-asyncio`, `httpx`

Exact compatible versions will be recorded in package manifests when each application is scaffolded.

## Required accounts and services

1. A Google account.
2. A Firebase project with Email/Password Authentication and Cloud Firestore in Native mode.
3. A Firebase web app configuration for the browser.
4. A Firebase service account for local backend development. Keep its credentials only in `backend/.env`.
5. A Gemini API key created in Google AI Studio. Keep it only in `backend/.env`.

The Firebase Spark plan is sufficient for initial local development in many cases. Confirm Gemini Live availability and quota for the selected model in Google AI Studio before the voice phase; quotas and billing requirements can change.

## Phase plan

1. Project structure and environment setup — complete
2. Firebase configuration — complete
3. FastAPI backend skeleton — complete
4. React frontend skeleton — complete
5. Authentication — complete
6. Journal functionality — complete
7. Text analysis API — complete
8. Emotion analysis — complete
9. Daily mood aggregation — complete
10. Dashboard — complete
11. Gemini voice assistant — complete
12. Conversation transcript persistence — complete
13. End-to-end testing — complete
14. UI cleanup — complete

## Privacy baseline

- Secrets never belong in frontend source code or Git.
- The backend will verify Firebase ID tokens before accessing user data.
- Raw private journal text will not be written to application logs.
- Obvious PII will be masked before text is sent for downstream analysis when practical.
- Rule-based PII masking is imperfect and must not be represented as guaranteed anonymization.
- Emotion outputs are text-derived signals, not diagnoses.

## Backend development

Run these commands in PowerShell:

```powershell
cd "C:\Users\Ravi Gupta\Desktop\Mindmate\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation or
`http://127.0.0.1:8000/api/health` for the health check.

Run the backend tests from the same activated terminal:

```powershell
python -m pytest -q
```

## Frontend development

Run these commands in a separate PowerShell terminal:

```powershell
cd "C:\Users\Ravi Gupta\Desktop\Mindmate\frontend"
npm install
npm run dev
```

Open `http://localhost:5173`. Run the frontend quality checks with:

```powershell
npm run test
npm run test:coverage
npm run typecheck
npm run lint
npm run build
npm run check:bundle
```

## End-to-end verification

Run the complete local quality gate from the project root:

```powershell
cd "C:\Users\Ravi Gupta\Desktop\Mindmate"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\verify.ps1
```

The gate runs Ruff linting and formatting, Mypy, backend tests with an 80%
coverage floor, frontend behavioral and API-contract tests with coverage floors,
TypeScript checking, ESLint, a production Vite build, a 250 KiB gzip JavaScript
chunk budget, and Python/npm production dependency audits. GitHub Actions runs
the same checks for every push to `main` and every pull request. Dependabot keeps
Python, npm, and workflow dependencies current; CodeQL and Gitleaks scan code and
Git history for security issues. The backend suite includes
an authenticated flow covering journal creation, journal analysis, conversation
persistence, conversation analysis, daily aggregation, and dashboard history.
It uses in-memory test doubles, so it never writes test records to Firebase or
spends Gemini quota.

Phase 13 also verifies:

- protected endpoints reject missing authentication;
- data remains scoped to the verified Firebase UID;
- blank, oversized, malformed, and chronologically invalid inputs are rejected;
- raw private text is excluded from persisted analysis documents;
- daily rebuilds are deterministic and do not double-count;
- Gemini Live tokens are single-use, short-lived, and configuration-constrained;
- private API responses use `Cache-Control: no-store` and standard hardening headers;
- production dependencies have no known npm audit findings;
- Python's installed dependency set is internally consistent;
- source files contain no obvious hardcoded API key or private-key patterns.

Manual acceptance remains necessary for provider-owned surfaces. Sign in with a
test account and exercise journal analysis using:

```text
English:  I had a really stressful day at work.
Hindi:    Aaj mera din bahut kharab tha.
Hinglish: Yaar aaj bahut stress ho raha hai.
```

Then complete and save a voice conversation, refresh the dashboard, and verify
the journal, conversation, analysis, and daily mood documents in Firestore.
Microphone permission, real Firebase writes, Gemini quotas, and device audio
cannot be fully validated by the isolated automated suite.

## Responsive UI

Phase 14 completes the MVP interface across authentication, dashboard, journal,
and voice-assistant routes. Desktop and tablet widths use the top navigation;
mobile widths use a thumb-friendly fixed bottom navigation with safe-area
padding. Shared cards and form controls adapt their spacing at small widths,
and the transcript panel scrolls independently so long conversations do not
stretch the entire page.

Keyboard users can skip directly to the main content and receive visible focus
indicators. Emotion bars expose progress semantics to assistive technology, and
the interface respects the operating system's reduced-motion preference.

Manual responsive acceptance:

1. Open browser developer tools and test widths of 375 px, 768 px, and 1440 px.
2. Confirm `/login` and `/register` never scroll horizontally and every input
   remains reachable.
3. Sign in and confirm the mobile bottom navigation appears below 768 px, while
   the desktop top navigation appears at 768 px and above.
4. Open Dashboard, Journal, and AI Assistant at each width and confirm cards,
   charts, form actions, transcript messages, and error states remain readable.
5. Navigate using only Tab and Enter; confirm the skip link and focus rings are
   visible and every action is reachable.
6. Enable reduced motion in the operating system and confirm nonessential
   animation is minimized.

## Authentication

Firebase provides email/password registration, login persistence, and logout.
Routes under `/dashboard`, `/journal`, and `/assistant` require a signed-in user.
The frontend sends Firebase ID tokens as bearer tokens for protected backend
requests. FastAPI verifies those tokens before trusting the UID.

The current authentication endpoint is:

```text
GET /api/auth/me
Authorization: Bearer <firebase-id-token>
```

Never send a Firebase password to FastAPI; passwords go only to Firebase Auth.

## Journals

Authenticated journal endpoints:

```text
POST /api/journal
GET  /api/journal?limit=20
```

The POST body is JSON:

```json
{
  "text": "Today felt calmer than yesterday."
}
```

Text is trimmed, must not be blank, and is limited to 10,000 characters. Raw
journal entries are stored beneath the verified user path:

```text
users/{uid}/journals/{journalId}
```

Each document contains `text`, `source: "journal"`, and an absolute UTC
`createdAt` timestamp. The API never accepts a UID from the browser.

## Text processing

The analysis endpoint is:

```text
POST /api/analyze
Authorization: Bearer <firebase-id-token>
```

Example body:

```json
{
  "text": "Aaj mera din bahut stressful tha",
  "source": "journal"
}
```

The processing order is language detection, local PII masking, then translation
when the detected language is not English. Only anonymized text is sent to the
translation provider. The response retains the original text for the requesting
user and includes language confidence, anonymized text, translated text, whether
translation ran, PII category counts, emotion scores, the dominant emotion,
confidence, and a 0–100 mood score. The persisted analysis deliberately omits
the original text.

Translation uses `gemini-3.8-flash` first and automatically retries with the
stable `gemini-3.5-flash-lite` fallback for transient capacity, rate-limit, and
server errors. Model names remain environment-configurable.

Supported MVP language labels are `en`, `hi`, `hinglish`, `other`, and
`unknown`. PII masking covers obvious emails, phone numbers, Aadhaar-like
numbers, basic street addresses, and names introduced by supported phrases.
This heuristic masking can miss PII and must not be treated as guaranteed
anonymization.

## Emotion analysis

Phase 8 classifies the privacy-processed English text into exactly five labels:
`joy`, `sadness`, `anger`, `fear`, and `neutral`. Gemini returns schema-validated
scores between 0 and 1. The largest score becomes the dominant emotion and its
value is exposed as confidence.

The application-level mood score is deterministic and explainable:

```text
round(clamp(50 + 50 × (joy − 0.8×sadness − 0.9×anger − 0.7×fear), 0, 100))
```

Neutral text therefore starts at 50. The result is an application estimate, not
a medical diagnosis. Results are stored under the verified user path:

```text
users/{uid}/analyses/{analysisId}
```

Each saved analysis includes its optional journal source ID, language metadata,
anonymized and translated text, PII category counts, emotion scores, dominant
emotion, confidence, mood score, and UTC timestamp. It does not duplicate the
raw journal text.

To test Phase 8 manually, run both applications, sign in, open **Journal**, write
an entry, and select **Save and analyze**. Confirm that the page displays the
mood score, five emotion bars, dominant emotion, confidence, and disclaimer.
Then confirm a corresponding document exists in the signed-in user's
`analyses` subcollection in Firestore.

## Daily mood aggregation

Every successful analysis triggers a rebuild of its UTC calendar date. The
rebuild reads that day's saved analyses and gives each analysis equal weight:

- `mood_score` is the rounded arithmetic mean of the individual mood scores.
- Each emotion is the arithmetic mean of that emotion's individual scores.
- `dominant_emotion` is the largest averaged emotion score.
- Journal, conversation, and total analysis counts are stored explicitly.

The result is overwritten at a deterministic path, so rebuilding the same date
does not double-count data:

```text
users/{uid}/dailyMood/{YYYY-MM-DD}
```

Authenticated endpoints:

```text
GET  /api/mood/daily?date=2026-09-20
POST /api/mood/daily/rebuild
```

The rebuild body is optional; omit the date to rebuild the current UTC date:

```json
{
  "date": "2026-09-20"
}
```

The automatic daily update is best-effort after the source analysis has been
saved. If Firestore is temporarily unavailable during aggregation, the analysis
remains intact and the rebuild endpoint can safely recover the daily record.
Dates use UTC for the MVP; profile-specific time zones are a future improvement.

## Dashboard

The protected `/dashboard` page loads the latest seven UTC daily records from:

```text
GET /api/mood/daily/history?days=7
```

It displays today's 0–100 mood estimate and dominant emotion, today's averaged
five-emotion distribution, a Recharts line graph containing only dates with
analyzed check-ins, and seven-day journal, conversation, and analysis totals.
Loading, retry, no-data, and no-check-in-today states are handled explicitly.
The chart bundle is lazy-loaded with the dashboard route to keep it out of the
initial authentication-page download.

## Gemini Live voice assistant

The protected `/assistant` page requests microphone access only after the user
selects **Start conversation**. It captures mono browser audio, downsamples it to
16 kHz signed PCM, and streams it directly to Gemini Live. Gemini's 24 kHz PCM
responses are queued through the Web Audio API, while input and output
transcriptions appear in the conversation panel.

The permanent Gemini API key never enters the browser. The authenticated
backend endpoint below creates a single-use credential with a one-minute window
for opening a new session and a fifteen-minute overall expiry:

```text
POST /api/live/token
```

The credential is constrained to `GEMINI_LIVE_MODEL`, audio responses,
input/output transcription, and MindMate's non-diagnostic system instruction.
The Assistant and Live SDK are lazy-loaded so they do not increase the initial
login or dashboard download. Phase 11 keeps transcripts in browser memory only;
Phase 12 adds explicit persistence and downstream analysis.

Manual test:

1. Run both applications and sign in.
2. Open `/assistant` and select **Start conversation**.
3. Allow microphone access when the browser asks.
4. Speak a short English, Hindi, or Hinglish sentence and pause.
5. Confirm your transcript, MindMate's transcript, and spoken response appear.
6. Select **End conversation** and confirm the microphone indicator turns off.

Microphone access requires `localhost`, another secure context, or HTTPS. Never
add `GEMINI_API_KEY` to a frontend `VITE_*` variable.

## Conversation persistence

Ending a Live session does not save it automatically. The user can review the
transcript and select **Save and analyze**. The complete transcript and
structured speaker turns are written to:

```text
users/{uid}/conversations/{conversationId}
```

Each document contains `source: "voice"`, `transcript`, `turns`, `startedAt`,
`endedAt`, and server-generated `createdAt`. Raw audio is never stored. The
backend derives the transcript from validated turns so the browser cannot send
conflicting transcript fields.

Authenticated endpoints:

```text
POST /api/conversations
GET  /api/conversations?limit=20
```

After persistence, only the user's transcribed turns—not MindMate's replies—are
sent through the existing PII masking, translation, emotion, and mood pipeline
with `source: "conversation"`. That analysis updates the corresponding daily
mood record and its conversation count. If analysis fails after storage, the UI
offers **Retry analysis** and reuses the saved conversation instead of creating
a duplicate.

Manual test:

1. Complete and end a voice conversation containing at least one user turn.
2. Select **Save and analyze**.
3. Confirm the saved/analyzed badge and mood summary appear.
4. Verify a document exists under the user's `conversations` subcollection.
5. Verify its ID is referenced by a `source: "conversation"` analysis.
6. Refresh the dashboard and confirm conversation and analysis totals increase.
