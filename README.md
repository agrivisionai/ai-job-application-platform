# AI Job Application & Recruiter Networking Platform

A personal job-search system: it polls applicant-tracking systems for new postings, scores them against your profile, prepares tailored applications, and tracks recruiter outreach — with a human approving anything that leaves the machine.

> **Status: foundation layer.** The configuration, security, encryption, logging and time subsystems are implemented and are what this README describes in detail. The ingestion, scoring, application and outreach layers are designed — every knob for them exists in `.env.example` — but not yet built. There is no API entrypoint yet. See [Roadmap](#roadmap) for what is and isn't done.

---

## Why this exists

Job searching at volume is a data pipeline problem wearing a trench coat. Postings arrive continuously across dozens of ATS instances, most are irrelevant, the relevant ones decay within days, and the actual work — tailoring a CV, finding the right recruiter, following up on the right day — is mechanical but easy to drop.

This automates the mechanical parts and deliberately refuses to automate the parts that should stay human.

## The design decision that shapes everything else

**Every job source is classified by what its operators actually permit, and the code enforces the classification.**

| Tier | Sources | How it works |
|---|---|---|
| **Public JSON APIs** | Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee, RemoteOK, Arbeitnow, Himalayas, Jobicy | Documented, no-auth endpoints. Polled directly. On by default. |
| **Licensed APIs** | Adzuna, Jooble, USAJOBS, The Muse | Need your own key. Off by default. |
| **Manual only** | LinkedIn, Indeed, ZipRecruiter, Dice, Glassdoor | No public jobs API, and their terms forbid automated access. The platform builds the search URL and an operator checklist. **A human runs the search and any submission. No other mode is supported.** |

That third row is the point. Scraping these sites is technically straightforward and is what most tools in this space quietly do. The `SOURCE_*_MODE=manual` settings have no `auto` value to switch them to — the restriction is structural, not a default someone can flip.

Supporting rails, all in `.env.example`:

- `RESPECT_ROBOTS_TXT=true` and a `USER_AGENT` that honestly identifies the client and its purpose
- `AUTO_SUBMIT_ENABLED=false` and `APPLICATION_MODE=assisted` — nothing is submitted without a human
- `OUTREACH_REQUIRES_APPROVAL=true` — no message reaches a recruiter unreviewed
- Hard caps: `MAX_APPLICATIONS_PER_DAY`, `MAX_APPLICATIONS_PER_WEEK`, `MAX_CONNECTION_REQUESTS_PER_DAY`, `MAX_OUTREACH_MESSAGES_PER_DAY`
- Two kill switches: `AUTOMATION_PAUSED` stops scheduled work, `EXTERNAL_ACTIONS_BLOCKED` stops anything leaving the process
- Quality gates: `MIN_MATCH_SCORE_TO_PREPARE=70`, `MIN_MATCH_SCORE_TO_AUTO_SUBMIT=85`

## Architecture

```
FastAPI (API)  ──┐
                 ├── Postgres + pgvector   embeddings, postings, applications
Celery workers ──┤   Redis                 broker, results, rate-limit state
  (scheduled)    └── ./data                uploads, generated documents, résumés
Next.js (frontend, scaffolded)
```

**Stack:** FastAPI · Pydantic v2 / pydantic-settings · SQLAlchemy 2 + Alembic · Postgres with pgvector (SQLite fallback for local work) · Celery + Redis · httpx + tenacity · Anthropic and OpenAI SDKs · structlog + prometheus-client · pytest

### What's implemented

| Module | Lines | What it does |
|---|---|---|
| `core/config.py` | 235 | Typed Pydantic settings for every subsystem. No secret is hard-coded; nothing reaches the frontend. |
| `core/crypto.py` | 59 | Fernet encryption for OAuth refresh tokens and API credentials at rest, plus `mask()` for safe display. |
| `core/security.py` | 44 | bcrypt password hashing and HS256 JWT access tokens. |
| `core/logging.py` | 40 | Structured logging with a greppable `key=value` event format; JSON mode for production. |
| `core/clock.py` | 56 | UTC storage, local display, and timezone-correct day/week boundaries. |

Three decisions in there worth calling out, because they're the ones I'd defend in review:

**Encryption refuses to degrade.** `crypto.py` will not write a plaintext secret. Outside development it raises `EncryptionNotConfigured` with the exact command to generate a key. In dev it derives a deterministic key from `SECRET_KEY` so local setup needs no extra step. A missing key is a configuration error, not a reason to silently store credentials in the clear.

**`clock.py` exists because rate limits are a timezone problem.** "20 applications per day" means a local calendar day, but every timestamp is stored in UTC. `local_day_bounds()` and `local_week_bounds()` return the UTC range for a local day or week, so the cap means the same thing in January and July and doesn't reset at an arbitrary hour.

**The LLM provider has an `offline` mode.** `LLM_PROVIDER=offline` and `EMBEDDING_PROVIDER=offline` are deterministic, need no network and no API key. Tests run without credentials and without spend, and the system has a defined fallback when a provider is down — rather than tests that quietly skip whenever a key is absent.

### Scaffolded, not yet built

`backend/app/` beyond `core/` · `frontend/app`, `frontend/components`, `frontend/lib` · `docs/` (including the `docs/INTEGRATIONS.md` referenced by `.env.example`)

## Getting started

Requires Python 3.11+. Postgres and Redis are optional for first run — SQLite and the offline LLM provider cover local work.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt             # or requirements-min.txt
cp .env.example .env
```

Then generate the two keys and paste them into `.env`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"                        # SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"   # ENCRYPTION_KEY
```

Defaults are chosen so a fresh clone runs with no accounts: SQLite instead of Postgres, `LLM_PROVIDER=offline`, only the no-auth job sources enabled, every licensed integration off.

**There is no server to start yet** — the API entrypoint is not written. The core modules are importable and tested in isolation.

## Configuration

`.env.example` is the reference and is commented throughout. Variables needing an account or key are marked `[CREDENTIAL]`. Grouped as: Core · Database · Redis/Celery · Storage · LLM provider · Job sources · Application automation · Networking · Email integration · Notifications · Safety rails.

`.env` is gitignored; `.env.example` is committed and contains no real values.

## Roadmap

- [x] Typed configuration covering every subsystem
- [x] Credential encryption at rest with no plaintext fallback
- [x] Auth primitives — bcrypt hashing, JWT
- [x] Structured logging and timezone-correct time handling
- [ ] Data model and Alembic migrations
- [ ] ATS source adapters for the ten public JSON endpoints
- [ ] Posting deduplication and pgvector embedding storage
- [ ] Match scoring against a parsed résumé
- [ ] Document generation — tailored CV and cover letter (`python-docx`, `reportlab`)
- [ ] Celery schedule and the rate-limit ledger
- [ ] Recruiter discovery and the approval-gated outreach queue
- [ ] Gmail / Outlook OAuth for reply tracking
- [ ] FastAPI routes and the Next.js dashboard

## Notes

Built for a single operator running their own job search. It is not a scraping tool and is not multi-tenant. The manual-mode classification above is a design constraint, not a configuration default — if you fork this, please keep it.
