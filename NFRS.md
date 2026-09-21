# MindMate non-functional requirements

These requirements apply to the browser app, FastAPI service, Firebase data,
and Gemini integrations. “Enforced” means the repository contains an automated
control or test. “Deployment target” requires production infrastructure or
measurement and must not be claimed solely from local tests.

## Security and privacy

| ID | Requirement and acceptance criterion | Status |
|---|---|---|
| SEC-01 | Every private API route verifies a Firebase ID token and derives the user ID from it; cross-user reads and writes are denied. | Enforced by API and Firestore-rule tests. |
| SEC-02 | Secrets are loaded only from backend environment settings. Gemini service credentials must never appear in a `VITE_*` variable or browser bundle. | Enforced by architecture and verification scan. |
| SEC-03 | API responses containing private data use `Cache-Control: no-store`, deny framing and MIME sniffing, and use a restrictive CSP. Production responses use HSTS. | Enforced by middleware tests. |
| SEC-04 | Declared HTTP request bodies larger than 65,536 bytes are rejected with HTTP 413 before route parsing. Domain models separately cap journal and analysis text at 10,000 characters. | Enforced by middleware and model tests. |
| PRIV-01 | Raw journal or conversation text must not appear in application logs. Request logs contain only request ID, method, path, status, and duration. | Enforced by logging design; inspect in release review. |
| PRIV-02 | Obvious PII is locally masked before translation or emotion processing. Persisted analyses omit original text, and raw audio is never stored. | Enforced by service and end-to-end tests. |
| PRIV-03 | Users must be able to export and permanently delete their account data; the retention period must be stated in the privacy notice. | Planned before production launch. |

## Performance and scalability

| ID | Requirement and acceptance criterion | Status |
|---|---|---|
| PERF-01 | On a representative production dataset, non-AI API requests meet p95 ≤ 2 seconds and p99 ≤ 5 seconds. AI analysis and token creation meet p95 ≤ 15 seconds, excluding a documented provider outage. | Deployment target; verify with load tests. |
| PERF-02 | Stalled browser API calls end after 15 seconds by default and surface a retryable, non-sensitive message. The limit is configurable from 1–120 seconds. | Enforced by frontend tests. |
| PERF-03 | At the 75th percentile, LCP is ≤ 2.5 seconds, INP ≤ 200 ms, and CLS ≤ 0.1 on supported desktop hardware; mobile LCP is ≤ 4 seconds on a mid-range device and 4G profile. | Deployment target; measure with Lighthouse and real-user monitoring. |
| PERF-04 | Dashboard and Assistant code remain route-lazy-loaded. A production build must complete without a single initial JavaScript chunk exceeding 250 KiB gzip unless the exception is recorded. | Lazy loading enforced; bundle budget planned. |
| SCALE-01 | The API supports 50 concurrent active users with <1% server-side errors while meeting PERF-01. Stateless API instances may be horizontally replicated. | Deployment target; verify before launch. |

## Reliability and recoverability

| ID | Requirement and acceptance criterion | Status |
|---|---|---|
| REL-01 | Monthly service availability target is 99.5%, excluding announced maintenance. Health monitoring checks `/api/health` without accessing user data. | Health endpoint enforced; SLO is a deployment target. |
| REL-02 | Daily mood rebuilds are deterministic and idempotent, so a failed best-effort aggregation can be retried without double-counting. | Enforced by tests. |
| REL-03 | Loading, empty, recoverable error, and retry states are provided for user-facing remote operations; provider errors do not expose credentials or internal exception text. | Enforced for current flows; review for every new flow. |
| REL-04 | Firestore backups provide RPO ≤ 24 hours and a documented restore exercise demonstrates RTO ≤ 4 hours. | Deployment target. |

## Accessibility and usability

| ID | Requirement and acceptance criterion | Status |
|---|---|---|
| A11Y-01 | Core login, journal, dashboard, and assistant journeys conform to WCAG 2.2 AA: keyboard operation, visible focus, semantic labels, logical heading order, and text/background contrast ≥ 4.5:1. | Partly enforced in UI; automated and manual audit required per release. |
| A11Y-02 | The app respects reduced-motion preferences and does not rely on color alone to communicate emotion, error, or completion state. | Enforced in current UI; manual release check. |
| USE-01 | Layouts remain usable without horizontal scrolling at 375, 768, and 1440 CSS pixels, including 200% browser zoom. | Manual release acceptance. |
| USE-02 | User-facing failures state what happened and offer a next action when recovery is possible. Mental-health outputs always retain the non-diagnostic disclaimer. | Enforced in current flows; review for every new flow. |

## Observability and supportability

| ID | Requirement and acceptance criterion | Status |
|---|---|---|
| OBS-01 | Every API response has an `X-Request-ID`. A valid caller ID is preserved; otherwise a UUID is generated. The same value appears in the metadata-only request log. | Enforced by middleware tests. |
| OBS-02 | Logs and alerts contain no journal text, transcript text, bearer token, API key, email address, or detected PII value. | Enforced by logging design; verify with a release log scan. |
| OBS-03 | Production alerts trigger when 5-minute server error rate exceeds 2%, p95 latency exceeds the applicable PERF-01 threshold, or health checks fail twice consecutively. | Deployment target. |

## Maintainability and portability

| ID | Requirement and acceptance criterion | Status |
|---|---|---|
| MAIN-01 | Every change passes backend tests, frontend tests, TypeScript checking, ESLint, and a production build through `verify.ps1`. | Enforced locally; CI integration recommended. |
| MAIN-02 | New business logic includes unit tests and changed critical modules maintain at least 80% line coverage. Public API contract changes update tests and this documentation. | Release requirement; coverage gate planned. |
| PORT-01 | Environment-specific origins, model names, limits, project identifiers, and secrets are configuration—not source edits. Startup rejects malformed required configuration. | Enforced by settings and environment examples. |
| PORT-02 | The supported baseline is Node.js 22 LTS, Python 3.11–3.12, and current Chromium-based browsers. A clean setup must work from the documented commands. | Manual release acceptance. |

## Responsible AI and safety

| ID | Requirement and acceptance criterion | Status |
|---|---|---|
| SAFE-01 | Emotion and mood outputs are described as text-derived estimates, never diagnoses or medical advice. | Enforced in API and UI copy. |
| SAFE-02 | The assistant does not claim clinical authority and directs imminent-risk users to local emergency or crisis resources without presenting itself as a substitute for professional care. | Prompt-level control; adversarial safety evaluation required before production. |
| SAFE-03 | Model or prompt changes run a documented evaluation set spanning English, Hindi, and Hinglish for schema validity, unsafe advice, privacy leakage, and material quality regressions. | Planned release gate. |

## Verification cadence

- Run `verify.ps1` on every change and in continuous integration.
- Run accessibility and responsive checks for each release candidate.
- Run load, Lighthouse, dependency, and AI safety evaluations before a production
  release and after material infrastructure or model changes.
- Review privacy retention, backup restore, alerting, and incident-response
  evidence at least quarterly.
