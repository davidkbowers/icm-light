# Railway Deployment Plan (Django, No Docker)

## Best Approach
Use Railway's native Python deployment path (Railpack), not Docker, with PostgreSQL, Gunicorn, WhiteNoise, and pre-deploy migrations.

For this repository, that is the safest and most maintainable path because the app currently uses SQLite and does not yet have WhiteNoise/PostgreSQL runtime wiring.

## Key Findings From Research + Repo Review
1. Current dependencies are missing production pieces for Railway.
2. Production defaults are not hardened yet (debug and secret handling).
3. Database is SQLite-only right now, which is not suitable for Railway production durability.
4. Static file directories/root are present, but WhiteNoise middleware is not configured.
5. Migration and collectstatic behavior already exists in Docker entrypoint logic, but for non-Docker Railway this should be moved to Railway build/pre-deploy commands.

## Plan: Railway Django Deployment Without Docker
Deploy through GitHub to Railway Railpack, convert DB config to PostgreSQL via DATABASE_URL, add WhiteNoise for static serving, and use Railway pre-deploy migrations with Gunicorn start command.

### Steps
1. Phase 1: Baseline decisions
2. Confirm whether production starts fresh or needs a one-time SQLite-to-PostgreSQL data migration.
3. Keep Docker files out of scope for deployment execution (Railway will not use them).
4. Phase 2: Django production hardening (depends on Phase 1)
5. Update settings defaults for production safety: debug off by default, no insecure fallback secret in production, explicit env parsing for hosts and CSRF origins.
6. Add WhiteNoise middleware and static storage settings.
7. Add missing packages for Railway runtime: WhiteNoise, psycopg, dj-database-url.
8. Add runtime pinning file for deterministic Python version on Railway.
9. Phase 3: Database migration strategy (depends on Phase 2)
10. Replace SQLite-only DATABASES config with DATABASE_URL parsing plus local fallback.
11. Add Railway PostgreSQL service and verify DATABASE_URL is injected to web service.
12. If historical data matters, perform a one-time data transfer before cutover; otherwise migrate fresh schema only.
13. Phase 4: Railway deployment setup (depends on Phases 2 and 3)
14. Connect repository to Railway service.
15. Build command: install dependencies and collect static files.
16. Pre-deploy command: run Django migrations (gates bad releases).
17. Start command: Gunicorn bound to Railway PORT.
18. Add Railway variables/secrets for DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS.
19. Phase 5: Verification and release readiness (depends on Phase 4)
20. Run Django deployment checks with production-like environment values.
21. Validate successful Railway build, pre-deploy migration, and healthy start.
22. Smoke test static files, form POST/CSRF, admin access, and DB writes.
23. Redeploy once to confirm data persistence and stable startup.

## Relevant Files
- config/settings.py for environment hardening, middleware, static strategy, and database wiring.
- requirements.txt for production dependencies.
- manage.py for migration and collectstatic commands used by Railway lifecycle steps.
- entrypoint.sh as reference only (Docker path, not used in this deployment).
- Dockerfile excluded from this deployment flow.
- runtime.txt (to be added) for Python version pinning.

## Verification Checklist
1. Local production-like boot with Gunicorn and environment variables.
2. Railway deploy logs confirm:
3. dependency install success
4. pre-deploy migration success
5. web process healthy
6. Application smoke tests on Railway URL:
7. static assets load
8. CSRF-protected forms submit
9. data persists across redeploy

## Scope Boundaries
- Included: non-Docker Railway deployment for this Django app.
- Excluded: Docker deploy path, worker queue architecture, CDN/front-proxy redesign.

## Recommended Railway Configuration (Concrete)

### Build Command
pip install -r requirements.txt && python manage.py collectstatic --noinput

### Pre-Deploy Command
python manage.py migrate --noinput

### Start Command
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3

### Required Environment Variables
- DJANGO_SECRET_KEY=<generated-secret>
- DJANGO_DEBUG=0
- DJANGO_ALLOWED_HOSTS=<your-railway-domain>,<custom-domain-if-any>
- CSRF_TRUSTED_ORIGINS=https://<your-railway-domain>,https://<custom-domain-if-any>
- DATABASE_URL=<provided automatically by Railway PostgreSQL service>

## Risks and Pitfalls To Avoid
1. Using SQLite in production on Railway (ephemeral filesystem risk).
2. Running Django runserver in production.
3. Skipping WhiteNoise/static handling.
4. Running migrations only at app startup instead of pre-deploy.
5. Missing ALLOWED_HOSTS or CSRF_TRUSTED_ORIGINS entries.
6. Leaving DEBUG enabled in production.
