# checklist-be

Backend for the checklist application, built with [Django](https://www.djangoproject.com/) 6.1.

> **Status:** early development. Implemented so far: the `users` table (custom Django user model), the
> authentication tables and endpoints (`sessions`, `email_verifications`, `password_resets`), and the public
> landing page content API. See [API](#api). The remaining ERD tables are listed under
> [Planned apps](#planned-apps).

## Requirements

- Python 3.12 or newer (required by Django 6.1)
- PostgreSQL, with a database containing a `checklist` schema (see [Database](#database))

Python dependencies are listed in [requirements.txt](requirements.txt).

## Getting started

From the project root:

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure the database connection (edit DATABASE_URL in .env)
Copy-Item .env.example .env         # macOS/Linux: cp .env.example .env

# 4. Create the tables in the schema
python manage.py migrate

# 5. Load the starter landing page content (it can be edited afterwards in the admin)
python manage.py seed_landing

# 6. (Optional) Create an admin user
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

See [Database migrations](#database-migrations) and [Running the server](#running-the-server) for details.

## Database migrations

Migrations create and change the tables in the `checklist` schema. Run these from the project root with the
virtual environment active and PostgreSQL running.

### First-time setup

```powershell
python manage.py migrate
```

This creates the `checklist` schema if it doesn't exist yet, then applies Django's built-in migrations
(`contenttypes`, `auth`, `admin`, `sessions`) and the project's own (`users`, `authentication`, `landing`), plus
the `django_migrations` bookkeeping table, all inside `checklist`. It is safe to run again; already-applied migrations are skipped.

> Run `migrate` before creating any other user data: the project uses a custom user model
> (`AUTH_USER_MODEL = 'users.User'`), which Django can't swap in after the first migration has been applied.

To check the result:

```powershell
python manage.py showmigrations        # [X] = applied, [ ] = pending
```

or in SQL:

```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'checklist';
```

### After changing models

Whenever you add or change a model, generate a migration, review it, then apply it:

```powershell
python manage.py makemigrations                  # create migration files from model changes
python manage.py sqlmigrate <app> <migration>    # (optional) preview the SQL, e.g. sqlmigrate auth 0001
python manage.py migrate                         # apply to the database
```

Notes:

- `makemigrations` only sees apps listed in `INSTALLED_APPS`. After `python manage.py startapp <name>`, add the
  app there first.
- Commit the generated files in each app's `migrations/` folder so everyone gets the same schema.
- `python manage.py migrate --plan` lists what would run without changing anything.

### Rolling back

Migrate an app back to an earlier migration (this can delete data in the affected tables):

```powershell
python manage.py migrate <app> <migration>       # e.g. migrate auth 0002
python manage.py migrate <app> zero              # undo every migration for that app
```

### Troubleshooting

- `ModuleNotFoundError: No module named 'dj_database_url'` (or `psycopg`, `dotenv`): the dependencies aren't
  installed in the Python you're running. Run `pip install -r requirements.txt`, with your virtual environment
  active if you use one.
- `permission denied for database`: `migrate` tries to create the schema when it is missing, which needs
  `CREATE` on the database. Create it yourself as a privileged user (`CREATE SCHEMA checklist;`) and run
  `migrate` again.
- Connection refused or authentication errors: PostgreSQL isn't running, or `DATABASE_URL` in `.env` is wrong.
- `permission denied for schema checklist`: the database user needs `CREATE` and `USAGE` on the schema.
- Tables appear in a different schema: `DB_SCHEMA` is set to something else, or a real environment variable is
  overriding `.env`.

## Running the server

Activate the virtual environment, make sure PostgreSQL is running and `.env` is configured, then start the
development server from the project root:

```powershell
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
python manage.py runserver
```

| URL                                  | What it serves                                                                           |
| ------------------------------------ | ---------------------------------------------------------------------------------------- |
| <http://127.0.0.1:8000/>             | Django's default "The install worked successfully!" page (no route is mapped to `/` yet) |
| <http://127.0.0.1:8000/admin/>       | Django admin (log in with the email and password from `createsuperuser`)                 |
| <http://127.0.0.1:8000/api/landing/> | The landing page content (JSON), see [API](#api)                                         |
| `http://127.0.0.1:8000/api/auth/...` | The authentication endpoints, see [API](#api)                                            |
| <http://127.0.0.1:8000/api/v1/>      | Swagger UI: browse and try every endpoint, see [Swagger](#swagger)                       |
| <http://127.0.0.1:8000/api/schema/>  | The OpenAPI schema (YAML) that Swagger UI reads; add `?format=json` for JSON             |

New endpoints go in the `urls.py` of the app they belong to, which [config/urls.py](config/urls.py) includes.

The server reloads automatically when code changes. Stop it with `Ctrl+C`.

Useful options:

```powershell
python manage.py runserver 8080            # use a different port
python manage.py runserver 0.0.0.0:8000    # listen on all interfaces (e.g. to test from another device)
```

When listening on a non-local address, add the hostname or IP you browse to into `ALLOWED_HOSTS` in
[config/settings.py](config/settings.py); `ALLOWED_HOSTS` is empty, so only `localhost`, `127.0.0.1` and
`[::1]` are accepted while `DEBUG` is on.

`runserver` is for development only. In production, serve the `config.wsgi.application` or
`config.asgi.application` entry point with a WSGI/ASGI server instead (none is included in
[requirements.txt](requirements.txt)).

If the server fails to start, check the following:

- `No module named 'dj_database_url'`: run `pip install -r requirements.txt`.
- `DATABASE_URL is not set`: create `.env` from `.env.example`.
- `connection refused` or authentication errors: PostgreSQL isn't running, or the credentials in `DATABASE_URL`
  are wrong.
- `You have N unapplied migration(s)` warning: run `python manage.py migrate` (see
  [Database migrations](#database-migrations)).

## Project structure

```
checklist-be/
├── manage.py              # Django's command-line utility
├── requirements.txt       # Python dependencies
├── .env.example           # Template for the local .env file (.env itself is git-ignored)
├── config/                # Project-wide configuration
│   ├── settings.py        # Settings (database, installed apps, middleware, ...)
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py            # WSGI entry point
│   └── asgi.py            # ASGI entry point
└── apps/                  # All project apps, one per area of the ERD
    ├── core/              # Shared building blocks (no tables of its own)
    │   ├── apps.py        #   creates the DB schema before migrations run
    │   ├── models.py      #   abstract UUIDModel base (UUID primary key)
    │   ├── exceptions.py  #   ApplicationError: base for expected, client-facing failures
    │   ├── exception_handler.py  # turns every API error into one JSON shape
    │   ├── api_docs.py    #   helpers that describe the API (errors) in Swagger
    │   ├── serializers.py #   RequestSerializer base (`validated(data)`)
    │   ├── views.py       #   PublicAPIView base for endpoints anyone can call
    │   └── tests/
    ├── users/             # The `users` table
    │   ├── models.py      #   User model
    │   ├── managers.py    #   create_user / create_superuser
    │   ├── admin.py       #   admin screens
    │   ├── migrations/
    │   └── tests/
    ├── authentication/    # `sessions`, `email_verifications`, `password_resets` + the auth endpoints
    │   ├── models.py      #   UserSession, abstract OneTimeToken, EmailVerification, PasswordReset
    │   ├── services/      #   the business logic, one class per file (see Architecture)
    │   ├── authentication.py  # JWTAuthentication: reads `Authorization: Bearer <token>`
    │   ├── serializers.py #   request bodies and response shapes
    │   ├── views.py       #   thin HTTP layer
    │   ├── urls.py        #   /api/auth/...
    │   ├── docs.py        #   what Swagger shows for each endpoint, and the Bearer-token scheme
    │   ├── exceptions.py  #   InvalidCredentialsError, ...
    │   ├── admin.py       #   read-only screens for the three tables
    │   ├── migrations/
    │   └── tests/
    └── landing/           # The public landing page, served from the database
        ├── models.py      #   LandingPage (copy), LandingFeature, LandingTestimonial
        ├── services.py    #   LandingPageService assembles the page
        ├── serializers.py #   the JSON shape
        ├── views.py, urls.py   # GET /api/landing/
        ├── admin.py       #   edit the copy, reorder and publish items
        ├── management/commands/seed_landing.py   # seeds the starter content
        ├── management/commands/_constants.py     # the starter features and testimonials
        ├── migrations/
        └── tests/
```

### Conventions

- Each app lives in `apps/<name>/` and is registered in `INSTALLED_APPS` as `apps.<name>`.
- Models, managers, admin, migrations and tests each get their own file or folder inside the app. Add
  `views.py`, `serializers.py` and `urls.py` to an app when it gets API endpoints, and a `services/` package (or
  `services.py`) for its business logic. See [Architecture](#architecture).
- Model tables are named after the ERD with `Meta.db_table` (for example `users`, not `users_user`).
- Models whose primary key is a UUID inherit from `apps.core.models.UUIDModel`.

To add an app (the folder must exist before `startapp`):

```powershell
mkdir apps\<name>                           # macOS/Linux: mkdir apps/<name>
python manage.py startapp <name> apps/<name>
```

Then set `name = 'apps.<name>'` in the generated `apps.py` and add `'apps.<name>'` to `INSTALLED_APPS`.

### What each file in an app is for

Using `apps/landing/` as the example, in the order a `GET /api/landing/` request passes through them:

| File               | What it is for                                                                                                                                           |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `urls.py`          | Maps the address to a view. `config/urls.py` mounts it at `/api/landing/` and this file routes the empty path to `LandingPageView`.                      |
| `views.py`         | The HTTP side only. `LandingPageView.get()` asks the service for the content, runs it through the serializer and returns the JSON. No business logic.   |
| `services.py`      | The logic. `LandingPageService.get_content()` collects the page copy, the published features and the published testimonials into one `LandingPageContent`. |
| `models.py`        | The database tables (`LandingPage`, `LandingFeature`, `LandingTestimonial`). Migrations are generated from this file.                                    |
| `serializers.py`   | Shapes the content into the JSON the frontend reads: nested `header`, `hero`, `features`, `testimonials` and `cta` blocks.                               |
| `admin.py`         | Configures the Django admin (`/admin/`) so the page text can be edited, reordered and published or hidden without touching code.                         |
| `apps.py`          | Registers the app with Django: its name (`apps.landing`) and label (`landing`). `INSTALLED_APPS` loads it.                                               |
| `__init__.py`      | Marks the folder as a Python package. It is empty, which is normal.                                                                                      |

The folders next to them:

| Folder                | What it is for                                                                                                          |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `migrations/`         | Creates and changes the tables and columns when you run `python manage.py migrate`.                                     |
| `management/commands/` | Custom `manage.py` commands. `seed_landing.py` inserts starter rows into tables that already exist; it never creates or changes tables. |
| `tests/`              | The app's tests.                                                                                                        |

Notes:

- `migrate` builds the structure and `seed_landing` fills it, so run them in that order. Both are needed.
- `__init__.py` is not strictly required on current Python (the app still loads and its tests pass without it), but it is
  the standard marker, every app here has one, and some tools (older test discovery, linters, IDEs, packaging) expect it.
  Keep it.
- Django treats every module in `management/commands/` that does not start with an underscore as a command, so helper
  modules there are named with a leading underscore (`_constants.py`). A plain `constants.py` would show up in
  `manage.py help` and crash if run.

### Planned apps

The ERD's tables are grouped into apps like this. `landing` is not in the ERD: it holds the landing page
content, which is not user data.

| App              | Tables                                                                |
| ---------------- | --------------------------------------------------------------------- |
| `users`          | `users` (done)                                                        |
| `authentication` | `sessions`, `email_verifications`, `password_resets` (done)           |
| `landing`        | `landing_page`, `landing_features`, `landing_testimonials` (done)     |
| `workspaces`     | `workspaces`, `workspace_members`                                     |
| `checklists`     | `checklists`, `checklist_items`, `tags`, `checklist_tags`, `comments` |

## API

Every endpoint speaks JSON and lives under `/api/`. Field names are `snake_case`.

### Swagger

With the server running, open <http://127.0.0.1:8000/api/v1/> to see every endpoint with its request body,
responses and error examples, and to send real requests from the page.

To call an endpoint that needs a login:

1. Open **POST /api/auth/login/** (or `signup`), click **Try it out**, and **Execute**.
2. Copy the `access_token` from the response.
3. Click **Authorize** at the top, paste the token (no `Bearer ` prefix needed) and confirm. The lock icons on
   `logout` and `me` now work, and the token is kept after a page reload.

Access tokens last 15 minutes. When one expires, use **POST /api/auth/refresh/** with the `refresh_token` and
authorize again with the new `access_token`.

The documentation is generated from the code with [drf-spectacular](https://drf-spectacular.readthedocs.io/), so
it only needs changing when an endpoint does:

- Request and response shapes come from the serializers.
- Titles, descriptions and error lists live in `apps/<app>/docs.py` (see `apps/authentication/docs.py`), applied to
  a view method as a decorator such as `@docs.sign_up`. Errors are built from the exception classes with
  `DocumentedError.of(...)` in `apps/core/api_docs.py`, so they match what the services raise.
- To check that the schema is complete, run `python manage.py spectacular --validate --fail-on-warn`. The test suite
  runs the same check.

Swagger UI's scripts come from the `drf-spectacular-sidecar` package, so the docs also work offline.

### Landing page

`GET /api/landing/` is public and returns everything the landing page renders, one block per section of the page:

```jsonc
{
  "header": { "login_label": "Log in", "signup_label": "Sign up free" },
  "hero": {
    "badge": "Now with shared workspaces",
    "title_prefix": "Checklists that keep your",
    "title_highlight": "whole team",          // shown in the brand gradient
    "title_suffix": "in sync",
    "description": "Plan launches, ...",
    "cta_label": "Read the Documentation"
  },
  "features": [{ "id": "...", "title": "Shared workspaces", "description": "...", "tone": "violet" }],
  "testimonials": { "title": "Trusted by teams who ship", "items": [{ "id": "...", "quote": "...", "author": "...", "role": "..." }] },
  "cta": { "title": "Ready to get organized?", "description": "...", "button_label": "Create your workspace" }
}
```

The copy and the lists are rows in the database, so they are edited in the admin (**Landing page**, **Landing
features**, **Landing testimonials**) without a deploy. Items are ordered by `position` and hidden while
`is_published` is off. `tone` is one of `violet`, `purple`, `fuchsia`, `pink`, `rose` (the frontend's `ToneName`).
Before anything is saved the endpoint serves the default copy, which is the text the frontend used to hard-code.
`python manage.py seed_landing` loads the starter features and testimonials; it never overwrites existing content.

### Authentication

| Endpoint                           | Needs token | Body                                  | Success                         |
| ---------------------------------- | ----------- | ------------------------------------- | ------------------------------- |
| `POST /api/auth/signup/`           | no          | `name`, `email`, `password`           | `201` user and tokens           |
| `POST /api/auth/login/`            | no          | `email`, `password`, `remember_me`    | `200` user and tokens           |
| `POST /api/auth/refresh/`          | no          | `refresh_token`                       | `200` user and new tokens       |
| `POST /api/auth/logout/`           | yes         |                                       | `204`                           |
| `GET /api/auth/me/`                | yes         |                                       | `200` user                      |
| `POST /api/auth/forgot-password/`  | no          | `email`                               | `204`, whether or not the address has an account |
| `POST /api/auth/reset-password/`   | no          | `token`, `new_password`               | `204`                           |
| `POST /api/auth/verify-email/`     | no          | `token`                               | `204`                           |

`user` is `{ "id", "email", "name", "email_verified" }` and `tokens` is
`{ "access_token", "refresh_token", "token_type": "Bearer", "expires_in": 900 }`.

How the tokens work:

- The **access token** is a short-lived (15 minutes) signed JWT. Send it as `Authorization: Bearer <access_token>`.
- The **refresh token** is a random string. Trade it at `/refresh/` for a new pair; each refresh token works once.
  A session lasts 1 day, or 30 days when `remember_me` is `true` ("Keep me signed in for 30 days"), and refreshing
  does not extend it.
- Only a SHA-256 digest of the refresh token and of the emailed tokens is stored, never the token itself.
- Every request looks the session up, so `/logout/` and a completed password reset (which ends all of the user's
  sessions) take effect immediately rather than when the access token expires.
- Sign-up logs the user straight in. Email verification is not required to log in; `email_verified` is there for
  features that want it.

Emails (verification, password reset) are printed to the server console in development. Their links point at the
frontend: `FRONTEND_URL/verify-email?token=...` and `FRONTEND_URL/reset-password?token=...`.

Login, sign-up and the password-reset endpoints are rate limited per client address (see `DEFAULT_THROTTLE_RATES` in
[config/settings.py](config/settings.py)); going over answers `429`.

### Errors

Every error has the same body, so a client only needs to read `error.message`:

```json
{ "error": { "code": "invalid_credentials", "message": "Invalid email or password.", "fields": {} } }
```

`fields` is filled for validation errors, as `{ "email": ["Enter a valid email address."] }`, and `message` is the
first of those messages.

| Status | `code`                                                                    | When                                          |
| ------ | ------------------------------------------------------------------------- | --------------------------------------------- |
| 400    | `validation_error`                                                        | a field is missing or malformed               |
| 400    | `weak_password`                                                           | the password fails `AUTH_PASSWORD_VALIDATORS` |
| 400    | `invalid_reset_link`, `invalid_verification_link`                         | the emailed token is unknown, used or expired |
| 401    | `invalid_credentials`                                                     | wrong email or password (the two look the same) |
| 401    | `invalid_refresh_token`                                                   | the refresh token is unknown, used or expired |
| 401    | `not_authenticated`, `authentication_failed`                              | missing, expired or revoked access token      |
| 409    | `email_already_registered`                                                | sign-up with an existing email                |
| 429    | `throttled`                                                               | too many requests; see the `Retry-After` header |

## Architecture

Requests flow through four layers, and each class has one job:

```
View  →  Serializer  →  Service  →  Model
HTTP     request/response  business     data and the
only     shape             rules        behaviour that belongs to it
```

- **Views** (`views.py`) validate the body, call one service method and shape the reply. No business rules.
- **Serializers** check the shape of a request and build the JSON of a response.
- **Services** (`services/`) are the use cases: `AuthService` (sign up, log in, refresh, log out),
  `PasswordResetService`, `EmailVerificationService`, plus the helpers they use (`SessionService`,
  `AccessTokenService`, `AuthMailer`). Services raise `ApplicationError` subclasses for expected failures.
- **Models** hold their own state rules, for example `UserSession.is_expired`, `OneTimeToken.is_usable` and
  `User.change_password()`.

How the object-oriented ideas are used:

| Idea                  | Where                                                                                                                      |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Inheritance           | `EmailVerification` and `PasswordReset` extend the abstract `OneTimeToken`; their services extend `OneTimeTokenService`. `LandingFeature` and `LandingTestimonial` extend `LandingContentItem`. Auth views extend `PublicAPIView`, request bodies extend `RequestSerializer`. |
| Abstraction           | `OneTimeTokenService` declares `model`, `lifetime` and `invalid_error` as abstract; it cannot be instantiated.              |
| Polymorphism          | `issue()` and `redeem()` are written once and work for whichever token table the subclass names.                           |
| Encapsulation         | Token generation and hashing, JWT signing and session rules are each hidden behind one class; callers never touch them.    |
| Composition / injection | `AuthService(sessions=..., access_tokens=..., email_verification=...)` builds its collaborators by default and accepts replacements, which is how the tests swap in a fake mailer. |
| Single responsibility | One class per concern: sessions, access tokens, mailing, the password-reset flow.                                           |
| Domain errors         | Failures are exception classes (`InvalidCredentialsError`, ...) carrying their own status code and message.                |

To add a use case: put the rules in a service class, expose them with a thin view, and describe the request body with
a `RequestSerializer`. Raise an `ApplicationError` subclass for failures the client should see, and add a decorator in
the app's `docs.py` so the endpoint shows up in [Swagger](#swagger) with those errors.

## Configuration

Settings live in [config/settings.py](config/settings.py). Values that differ per machine are read from
environment variables, which can be set in a `.env` file in the project root (loaded automatically; real
environment variables take precedence).

| Variable               | Required | Description                                                                                       |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------------- |
| `DATABASE_URL`         | yes      | `postgres://<user>:<password>@<host>:<port>/<database>`                                           |
| `DB_SCHEMA`            | no       | PostgreSQL schema Django works in. Defaults to `checklist`.                                       |
| `SECRET_KEY`           | no       | Signs access tokens and sessions. Falls back to an insecure development key: set it in production. |
| `FRONTEND_URL`         | no       | Where the frontend runs; emailed links point here. Defaults to `http://localhost:3000`.           |
| `CORS_ALLOWED_ORIGINS` | no       | Comma-separated origins allowed to call the API from a browser. Defaults to `FRONTEND_URL`.       |
| `DEFAULT_FROM_EMAIL`   | no       | Sender of the account emails. Defaults to `Checklist <no-reply@checklist.local>`.                 |

Other current defaults:

| Setting                            | Value                                        |
| ---------------------------------- | -------------------------------------------- |
| `DEBUG`                            | `True`                                       |
| `ALLOWED_HOSTS`                    | `[]` (localhost only while `DEBUG` is on)    |
| `TIME_ZONE`                        | `UTC`                                        |
| `LANGUAGE_CODE`                    | `en-us`                                      |
| Email backend                      | Console (emails are printed to the terminal) |
| `AUTH_ACCESS_TOKEN_LIFETIME`       | 15 minutes                                   |
| `AUTH_REFRESH_TOKEN_LIFETIME`      | 1 day (30 days with `AUTH_REMEMBER_ME_LIFETIME`) |
| `AUTH_EMAIL_VERIFICATION_LIFETIME` | 2 days                                       |
| `AUTH_PASSWORD_RESET_LIFETIME`     | 1 hour                                       |

Installed apps are Django's defaults (`admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles`),
the third-party `rest_framework`, `corsheaders`, `drf_spectacular` and `drf_spectacular_sidecar` (Swagger), and the
project apps `apps.core`, `apps.users`,
`apps.authentication` and `apps.landing`. `AUTH_USER_MODEL` is `users.User`.

### Database

The project uses PostgreSQL. `DATABASE_URL` is parsed with
[dj-database-url](https://github.com/jazzband/dj-database-url), for example:

```
DATABASE_URL=postgres://postgres:your-password@localhost:5432/management
DB_SCHEMA=checklist
```

Special characters in the password must be percent-encoded (for example `@` becomes `%40`).

Django is pointed at the schema through the connection's `search_path`, so `migrate` creates every table,
including Django's own (`django_migrations`, `auth_*`, `django_admin_log`, ...), inside `checklist` rather
than `public`. If the schema doesn't exist, `migrate` creates it first (this needs the `CREATE` privilege on
the database; otherwise create it yourself with `CREATE SCHEMA checklist;`).

### Users

The `users` table (`apps.users.models.User`) follows the ERD. Users log in with their email address, which is
stored in lowercase and must be unique.

| Column                                         | Notes                                                    |
| ---------------------------------------------- | -------------------------------------------------------- |
| `id`                                           | UUID primary key                                         |
| `email`                                        | unique, used as the login name                           |
| `name`                                         |                                                          |
| `password_hash`                                | hashed by Django; never stores the raw password          |
| `email_verified`                               | defaults to `false`                                      |
| `created_at`, `updated_at`                     | set automatically                                        |
| `is_active`, `is_staff`, `is_superuser`, `last_login` | not in the ERD; needed by Django's admin and permissions (`is_superuser` and `last_login` come with Django's auth mixins) |

Django's group and permission links are stored in the extra tables `users_groups` and
`users_user_permissions`.

Create an admin user (it prompts for email, name and password):

```powershell
python manage.py createsuperuser
```

### Tests

```powershell
python manage.py test
```

Tests run against a temporary `test_<database name>` database (for example `test_management`) that Django
creates and drops automatically, so your real data isn't touched. The database user needs the `CREATEDB`
privilege.

### Before deploying

These settings are development-only and must be changed for any shared or production environment:

- Set `SECRET_KEY` in the environment (the built-in fallback is public, and it signs the access tokens).
- Set `FRONTEND_URL` and `CORS_ALLOWED_ORIGINS` to the real frontend, and configure a real email backend in
  `MAILERS`. Password-reset and verification emails are only printed to the console until you do.
- Set `DEBUG = False`.
- Set `ALLOWED_HOSTS` to the hostnames the app is served from.
- Use a dedicated database user with a strong password, and a real email backend.
- Swagger (`/api/v1/`, `/api/schema/`) is public and lists every endpoint. If you don't want that in production,
  remove the two routes from [config/urls.py](config/urls.py) (or put them behind a login). With `DEBUG = False`,
  Django no longer serves static files, so run `python manage.py collectstatic` and serve them from your web
  server, otherwise Swagger UI loads without its scripts.

Django's own checks can flag remaining issues:

```powershell
python manage.py check --deploy
```

## Common commands

```powershell
python manage.py startapp <name> apps/<name>   # Create a new app (see Conventions above)
python manage.py makemigrations        # Generate migrations after changing models
python manage.py migrate               # Apply migrations
python manage.py test                  # Run the test suite
python manage.py shell                 # Open an interactive shell with Django loaded
```
