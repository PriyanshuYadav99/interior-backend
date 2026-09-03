# AI Interior Design Backend

Flask backend powering AI interior design generation (via Replicate), the
"Living insight" scenario feature, virtual tour / nearby-places search, an
admin dashboard, activity tracking, and area news — backed by Supabase.

## Getting started

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in real credentials
python app.py                   # dev server, http://localhost:5000
```

Production deploy uses `Procfile` (`gunicorn app:app`) — see the important
note on the scheduler below before relying on that for scheduled jobs.

## Environment variables

All loaded centrally in `config/settings.py`. See that file for the full
list and defaults; the important ones:

```
OPENAI_API_KEY, REPLICATE_API_TOKEN, GROQ_API_KEY
SUPABASE_URL, SUPABASE_SERVICE_KEY
CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_FROM
META_WHATSAPP_API_VERSION, META_PHONE_NUMBER_ID, META_ACCESS_TOKEN
GOOGLE_MAPS_API_KEY, NEWS_API_KEY
FRONTEND_URL, PORT
```

## Project structure

```
app.py                       Thin entrypoint: Flask app, CORS, blueprint
                              registration, + 4 small debug/scheduler routes
                              (see "known issue" below for why those 4 stay here)

config/
  settings.py                 Every env var, loaded once, with the exact
                               same defaults each file used to hardcode
                               individually

content/                      Static design content & prompt engineering —
                               not "config" in the env-var sense, so split
                               out of the old config.py into its own area
  design_content.py             Room layouts, styles, theme elements,
                                 reference image paths (was config.py)
  prompts.py                    Prompt construction logic

services/                     Business logic and external integrations
  external_clients.py           Supabase + Cloudinary client setup
  design_generation_service.py  Caching, DB persistence, Cloudinary upload,
                                 prompt processing, Replicate generation
                                 pipeline (was inline in app.py)
  email_service.py              Welcome email (was inline in app.py)
  whatsapp_service.py           Meta WhatsApp/SMS notification sending
  scheduler.py                  APScheduler setup for delayed notifications

routes/                       All Flask blueprints
  design_routes.py               Core: rooms/styles, registration, session
                                  tracking, image generation (NEW — this
                                  logic used to be @app.route directly)
  life_echo_routes.py            "Living insight" scenarios (was Life_Echo.py)
  virtual_tour_routes.py         Nearby places / directions (was virtual_tour.py)
  admin_routes.py                Admin dashboard & lead management
  activity_routes.py             User activity/tool-usage logging
  ai_routes.py                   AI lead scoring / WhatsApp message regen
  news_routes.py                 Area news by zip code

utils/
  decorators.py                 timeout_decorator (was inline in app.py)

scripts/                      Standalone dev/diagnostic scripts, not
                               imported by the running app
  find_cache_location.py
  test_api.py

images/                        Reference room images (unchanged)
data.sql                       DB schema (unchanged)
```

### Why this shape

- **`content/` vs `config/`** — the original `config.py` held design/prompt
  *data* (room layouts, style descriptions), not environment configuration.
  Renaming and relocating it makes `config/` mean what it says.
- **`services/`** holds anything that talks to an external system (Supabase,
  Cloudinary, Replicate, email, WhatsApp) or does non-trivial business logic,
  so route handlers stay thin and testable in principle.
- **`routes/`** is now consistent — every feature is a blueprint, including
  design generation, which previously was the one exception living directly
  on the `app` object.
- **`design_routes.py` is new**; every other route file already existed as
  a blueprint and was simply relocated, not rewritten.

## What changed vs. what didn't

Every route body, every helper function's internal logic, every API
response shape is **unchanged** — this pass only reorganized files, fixed
import paths, and removed genuinely dead code. Verified by:
- `python -m py_compile` on every file
- A fresh `pip install -r requirements.txt` into a clean virtualenv
- Actually importing the full Flask app with dummy credentials and
  confirming all 33 routes register with the same URLs as before
- Diffing the full route list against the original `app.py` to confirm all
  16 originally-inline routes are present and unchanged

Two small `__file__`-relative path calculations *did* need adjusting as
part of the move (in `content/design_content.py` and
`services/design_generation_service.py`) — files that moved one folder
deeper than they used to needed their "find the project root" logic
updated so they still resolve to the *same* actual file paths as before.
This was necessary for the move itself to not silently break image
loading; it is not a behavior change.

## Known issues found during this pass (not fixed — flagged for you)

These predate this restructure. None were introduced by it, and none were
silently changed — surfacing them here instead so nothing gets missed.

1. **The notification scheduler likely never runs in production.**
   `app_scheduler` (used by `/api/scheduler-status` and initialized via
   `init_scheduler()`/`start_scheduler()`) is only ever assigned inside
   `if __name__ == '__main__':` in `app.py`. Your `Procfile` runs the app
   via `gunicorn app:app`, and gunicorn never triggers that block — so in
   production, the background job that processes scheduled WhatsApp/SMS
   notifications is likely never started. `/api/scheduler-status` will
   report `"Scheduler not initialized"` in production as a result. This is
   why the 4 debug/scheduler routes were deliberately kept in `app.py`
   rather than moved into `routes/` — moving them would have required
   either replicating this exact (buggy) scoping elsewhere or fixing it
   outright, and this pass is structure-only.

2. **Two deployment targets configured, possibly unintentionally**: both
   `Procfile` (gunicorn, for Railway/Heroku-style hosts) and `vercel.json`
   (Vercel serverless) are present. If actually deployed on Vercel, note
   that serverless functions are stateless/short-lived — `APScheduler`'s
   background thread approach (used by `services/scheduler.py`) generally
   doesn't work reliably in that environment.

3. **`request_notification`/log text inconsistency**: `simple_register` in
   `routes/design_routes.py` calls `schedule_user_notification(..., delay_minutes=2, ...)`
   but immediately logs `"scheduled ... in 30 minutes"`. The actual delay is
   2 minutes; the log message is stale.

4. A broken **fallback** reference-image path in `content/design_content.py`:
   `ROOM_IMAGES` (the "default" reference image set) points at
   `images/MADHUBANbedroom.webp` etc., but the actual files live nested at
   `images/madhuban/MADHUBANbedroom.webp`. In practice this path is likely
   unreachable dead code anyway, since `generate_design` only accepts
   `client_name` in `['skyline', 'ellington', 'sothebys']` — `'default'` is
   never a valid value reaching this fallback.

5. `find_cache_location.py` (in `scripts/`) is a diagnostic script that
   greps `app.py` for cache-variable definitions — those now live in
   `services/design_generation_service.py`, so the script's assumptions are
   stale. It's a standalone dev tool, not imported by the running app, so
   this doesn't affect the server; flagging in case you still use it.
