# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Django 6.1 + Django REST Framework JSON API (`apps/users`, `apps/authentication`, `apps/landing`, shared code in `apps/core`). PostgreSQL only. [README.md](README.md) is the detailed reference for the endpoint tables, token behaviour, error codes and the settings/env-var table; this file covers what you need to work in the code.

## Commands

Run from the project root. The venv is `.venv` (activate with `.venv\Scripts\Activate.ps1`, or call `.venv\Scripts\python.exe manage.py ...` directly).

```powershell
python manage.py migrate
python manage.py seed_landing            # starter landing content; idempotent, never overwrites edits
python manage.py runserver               # Swagger UI at /api/v1/, admin at /admin/

python manage.py test --noinput                                   # whole suite (~30-60 s)
python manage.py test apps.landing --noinput                      # one app
python manage.py test apps.landing.tests.test_api.LandingPageApiTests.test_only_allows_get --noinput   # one test

python manage.py makemigrations --check --dry-run                 # fails if a model change has no migration
python manage.py spectacular --validate --fail-on-warn            # OpenAPI schema check (the test suite runs it too)
```

- `DATABASE_URL` is required (settings raise `ImproperlyConfigured` without it); copy `.env.example` to `.env`. There is no SQLite fallback.
- Tests create and drop `test_<dbname>`, so the DB user needs `CREATEDB`.
- No linter or formatter is configured.

## Architecture

### Layers (auth is the reference implementation)

`View → Serializer → Service → Model`. Views are thin: validate with `SomeSerializer.validated(request.data)` (`apps/core/serializers.py:RequestSerializer`), call one service method, serialize the result. Business rules live in `services/`; state rules live on models (`UserSession.is_expired`, `OneTimeToken.is_usable`, `User.change_password()`).

- Services are instantiated once as class attributes on views (`service = AuthService()`). `AuthService` builds its collaborators by default but accepts replacements through its constructor, which is how tests swap in fakes.
- `OneTimeTokenService` (abstract) implements `issue()`/`redeem()` once for email verification and password reset; subclasses only supply `model`, `lifetime` and `invalid_error`.
- Tokens (refresh, emailed) are random opaque strings; only their SHA-256 digest is stored.

### Errors: one shape, documented from the same classes that raise them

- Services raise `ApplicationError` subclasses (`apps/core/exceptions.py`) that carry `status_code`, `code` and `message`.
- `apps/core/exception_handler.py:handle_exception` (set as `EXCEPTION_HANDLER`) turns those, and DRF's own errors, into `{"error": {"code", "message", "fields"}}`. Anything else is left to Django (a 500 is Django's page, not this JSON).
- Swagger error entries are built from the same exception classes via `DocumentedError.of(SomeError)` and `error_responses(...)` in `apps/core/api_docs.py`, so docs cannot drift from behaviour. Each app keeps these as decorators in its own `docs.py` (`@docs.log_in`) and the view applies them.

### Auth and permissions

- DRF defaults are closed: `JWTAuthentication` + `IsAuthenticated`. Public endpoints extend `apps.core.views.PublicAPIView` (no authenticators, `AllowAny`, `ScopedRateThrottle`); set `throttle_scope` on the subclass and add its rate to `REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']`.
- `JWTAuthentication` decodes the access token **and then looks up the `UserSession` on every request**, so logout and password reset revoke access immediately. `request.auth` is the `UserSession`.
- Because `PublicAPIView` has no authenticators, DRF turns a would-be 401 into a 403 on those views.

### Landing page (`apps/landing`)

- Page copy is a single `LandingPage` row edited in the admin. `LandingPage.load()` returns the saved row or an **unsaved instance holding the defaults**, so reading never writes and the page works before `seed_landing`. Features and testimonials extend the abstract `LandingContentItem` (ordered by `position`, hidden when `is_published` is off).
- The error messages for `GET /api/landing/` are plain constants in `apps/landing/error_messages.py` (`ERROR_COPY`), not database rows and not part of the 200 body. `LandingPageView.handle_exception` swaps them into real error responses, and `docs.py` documents the same table in Swagger. Several documented statuses (401, 403, 404, 500) are not raised by the endpoint itself; that is intentional.

### Database

- Tables live in the PostgreSQL schema named by `DB_SCHEMA` (default `checklist`) through the connection's `search_path` option in `config/settings.py`. A `pre_migrate` signal in `apps/core/apps.py` creates the schema if missing.
- `AUTH_USER_MODEL = 'users.User'` (email is the login name, stored lowercase): migrate before creating any user data, since the user model can't be swapped after the first migration.
- All models use UUID primary keys (`apps/core/models.py:UUIDModel`).

## Conventions that tests enforce

- **Adding an endpoint:** put the rules in a service, expose it with a thin view, describe the body with a `RequestSerializer`, add a decorator in the app's `docs.py`, and add `(path, method)` to `ENDPOINTS` in `apps/core/tests/test_docs.py`; that test fails if documented endpoints and `ENDPOINTS` differ. The schema must also generate with no warnings.
- **Endpoint tests** extend `AuthAPITestCase` (`apps/authentication/tests/base.py`): it uses `APIClient` and clears the cache in `setUp`, because DRF throttle counters live in the cache.
- **Changing models** needs a generated, committed migration (`makemigrations --check` should report no changes). Review the generated file before applying it.
- Account emails go to the console in development (`MAILERS` in settings); tests read them from `mail.outbox`.
