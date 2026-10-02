# Deployment Guide for Interior Backend

## 1. Project overview

This backend is a Flask application that powers:

- AI interior design generation
- user registration and session tracking
- LifeEcho scenario generation
- virtual tour and location features
- admin lead dashboards
- WhatsApp/SMS notifications
- scheduled jobs and notifications
- Supabase-backed persistence

This repository is functional, but it is not yet production-grade in its current form. It has several signs of a fast prototype / vibe-coded codebase that needs refactoring before it can be considered a well-engineered product.

---

## 2. Recommended deployment target

Use one deployment model only.

Recommended: deploy as a standard Flask service behind Gunicorn on a Linux host or PaaS like Render, Railway, or a VPS.

Do not run both of these together:

- `Procfile` with Gunicorn
- `vercel.json` for serverless deployment

This project is not a good match for Vercel serverless without major refactoring because it uses in-process scheduler state and long-lived background threads.

---

## 3. Environment setup

### Required environment variables

Create a `.env` file from the project root:

```bash
cp .env.example .env
```

If `.env.example` does not exist, create it manually with:

```env
PORT=5000
FLASK_ENV=production
FLASK_DEBUG=0

# AI APIs
OPENAI_API_KEY=
REPLICATE_API_TOKEN=
GROQ_API_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# Cloudinary
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=
EMAIL_PASSWORD=
EMAIL_FROM=

# WhatsApp / SMS
META_WHATSAPP_API_VERSION=v21.0
META_PHONE_NUMBER_ID=
META_ACCESS_TOKEN=

# Maps / location
GOOGLE_MAPS_API_KEY=

# News
NEWS_API_KEY=

# Frontend
FRONTEND_URL=http://localhost:5177/
```

### Validate environment

Before running production, verify all required keys are present:

```bash
python - <<'PY'
import os
required = [
    'SUPABASE_URL','SUPABASE_SERVICE_KEY','GROQ_API_KEY',
    'REPLICATE_API_TOKEN','CLOUDINARY_CLOUD_NAME','CLOUDINARY_API_KEY',
    'CLOUDINARY_API_SECRET'
]
missing = [k for k in required if not os.getenv(k)]
if missing:
    print('Missing:', missing)
else:
    print('All required env vars present')
PY
```

---

## 4. Local development setup

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run the app locally

```bash
python app.py
```

or for production-like behavior:

```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 1 --threads 16 --timeout 200
```

---

## 5. Production deployment

### Option A: Linux VPS / Docker host

Use Gunicorn and a Process Manager such as systemd or Supervisor.

Example:

```bash
export PORT=5000
gunicorn app:app \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 8 \
  --timeout 200 \
  --access-logfile - \
  --error-logfile -
```

### Option B: Render / Railway / similar PaaS

Configure:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 16 --timeout 200`
- Add all environment variables in the platform UI

### Important production note

This project currently has scheduler logic that is initialized only inside `if __name__ == '__main__':` in [app.py](app.py). That means the scheduler will likely not start under Gunicorn in production.

Fix this before production by moving scheduler bootstrap into an application factory and startup hook rather than relying on `__main__`.

---

## 6. Health checks and operational monitoring

Add a health endpoint like:

```python
@app.get('/health')
def health():
    return {
        'status': 'ok',
        'service': 'interior-backend',
        'supabase': bool(supabase)
    }
```

Recommended endpoints to expose:

- `/health`
- `/ready`
- `/api/scheduler-status`

Recommended logs:

- request ID per request
- response time
- error-level stack traces
- summary of external API failures

---

## 7. Important production issues to fix before launch

### 7.1 Scheduler bootstrapping

Current issue:

- Scheduler is created in [app.py](app.py) inside the main guard.
- Gunicorn imports the module, so `__main__` does not run.

Result:

- background jobs may never start in production.
- scheduled notifications can silently stop.

Fix:

- Move to `create_app()` factory pattern.
- Initialize scheduler in app startup after app creation.
- Keep job registration in a dedicated module.

### 7.2 Mixed responsibilities in app.py

[app.py](app.py) currently contains:

- Flask app creation
- CORS setup
- blueprint registration
- scheduler debug routes
- WhatsApp test routes
- app startup logic
- production debug endpoints

This is a classic sign of a quickly assembled monolith. It is harder to test, mock, secure, and deploy correctly.

Fix:

- `app.py` should only create the app and run it.
- Routes should go in modules under [routes/](routes/)
- Service logic should live under [services/](services/)
- config should be centralized under [config/settings.py](config/settings.py)
- startup bootstrap should be isolated in a startup module

### 7.3 Debug/test endpoints remain in production code

Examples include test routes in [app.py](app.py) for WhatsApp/SMS testing and scheduler diagnostics.

These should be removed or protected behind strict admin auth before production.

### 7.4 Inconsistent deployment model

The repo contains both:

- [Procfile](Procfile)
- [vercel.json](vercel.json)

This creates ambiguity. Pick one and remove the other.

### 7.5 Unpinned dependencies

[requirements.txt](requirements.txt) uses broad version ranges (`>=`). That is not ideal for stable deployment.

Fix:

- pin production versions tightly
- use a lock file or constraints file
- separate dev and prod dependencies

### 7.6 No automated tests

There is no real test suite for routes, services, or deployment assumptions.

Fix:

- add unit tests for scoring logic
- add route tests for key endpoints
- add integration tests for Supabase and external clients
- run tests in CI

### 7.7 Missing quality gates

There is no clear CI, linting, formatting, or PR validation workflow.

Recommended setup:

```bash
pip install black flake8 pytest pytest-cov
```

Then add:

- `black .`
- `flake8 .`
- `pytest --cov=.`

---

## 8. Engineering refactor plan to make this look like a proper software project

### Phase 1: stabilize the foundation

1. Add `.env.example`
2. Validate environment on startup
3. Remove debug/test routes from production
4. Decide one deployment platform
5. Fix scheduler initialization
6. Add health checks

### Phase 2: clean architecture

1. Create `create_app()` factory
2. Move app setup into a proper startup module
3. Centralize dependency injection
4. Keep route files thin
5. Move all external API calls into service modules
6. Add typed request/response models if needed

### Phase 3: reliability and maintainability

1. Add logs with request IDs and structured output
2. Add retry logic for Groq / Supabase / Cloudinary failures
3. Add error boundaries and graceful degradation
4. Add rate limiting and request validation
5. Add database transaction safety for writes

### Phase 4: professional delivery

1. Add CI pipeline
2. Add test suite with coverage target
3. Add linting and formatting
4. Add Dockerfile and docker-compose
5. Add architecture documentation
6. Add rollback/release process

---

## 9. Suggested folder structure improvement

Current structure is close to workable, but a more professional structure would look like:

```text
app/
  __init__.py
  factory.py
  config.py
  routes/
    admin.py
    design.py
    users.py
    activity.py
  services/
    ai.py
    notifications.py
    storage.py
    scheduler.py
  models/
  schemas/
  utils/
  tests/
    unit/
    integration/
```

The important idea is not the exact folder names, but the separation of:

- app creation
- configuration
- routes/controllers
- business logic/services
- infrastructure integrations
- tests

---

## 10. Production readiness checklist

Before deployment, verify all of the following:

- [ ] Single deployment target selected
- [ ] Scheduler starts in prod
- [ ] `.env` validated and `.env.example` included
- [ ] No debug/test routes exposed
- [ ] Health endpoint works
- [ ] Logs are structured and searchable
- [ ] Dependencies are pinned
- [ ] CI pipeline runs lint/test/build
- [ ] Secrets are not committed to repo
- [ ] Supabase and external APIs are configured and tested
- [ ] Application can recover from service failures
- [ ] Error monitoring is configured

---

## 11. Summary

This project is functional and has a lot of useful domain logic, but it currently has multiple signs of an MVP or vibe-coded codebase:

- route logic and startup logic mixed together
- debug/test paths left in production app
- unclear deployment target
- scheduler reliability issues under Gunicorn
- no real CI/test pipeline
- no strict quality gates or dependency pinning

It can absolutely be made to look and behave like a professional engineering project, but only through disciplined cleanup and a proper production architecture.

The most important immediate fixes are:

1. fix scheduler startup
2. remove debug endpoints
3. define a single deployment strategy
4. add tests and CI
5. refactor app creation into an application factory

---

## 12. Useful commands

```bash
# local run
python app.py

# production run
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 16 --timeout 200

# lint
flake8 .

# format
black .

# tests
pytest -q
```

If you want, the next step should be to refactor the app into an application factory and add a proper test suite before deployment.
