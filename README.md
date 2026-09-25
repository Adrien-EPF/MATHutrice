# MATHutrice

LLM-based tutor that helps EPF first-year students practise mathematical tools through notions, competences and training. Students pick a module, see their progression, and train with exercises generated and evaluated by an LLM; teachers upload course material and follow their students.

The project's vocabulary (**connexion de développement**, **impersonation**, **LLM endpoint**…) is defined in [`CONTEXT.md`](CONTEXT.md).

## Run it locally

Requires [uv](https://docs.astral.sh/uv/). It installs the Python version pinned in `.python-version` and the dependency versions locked in `uv.lock`.

```sh
git clone -b course-2026 <fork URL> mathutrice
cd mathutrice
uv sync
. .venv/bin/activate        # Windows: .venv\Scripts\activate
cp .env.example .env
```

Edit `.env` and set `LLM_API_KEY` (see below). Then, from the repository root:

```sh
uvicorn mathutrice.app:app --port 8000
```

Open <http://localhost:8000/>. To check that your clone works end to end, follow [`docs/smoke-test.md`](docs/smoke-test.md).

If `uv sync` reports `No interpreter found for Python 3.14.7`, run `uv self update` and retry. Without uv, `pip install -e .` in a virtual environment running that Python version works too, from `pyproject.toml` rather than the lockfile.

## Environment variables

`.env.example` lists every variable the application reads. The application refuses to start when a required one is missing.

| Variable | Default in `.env.example` | Purpose |
| --- | --- | --- |
| `LLM_API_KEY` | _empty_, **required** | Key for the **LLM endpoint**. Get a Mistral key at <https://console.mistral.ai>. |
| `LLM_BASE_URL` | `https://api.mistral.ai/v1` | Any OpenAI-compatible API. |
| `LLM_MODEL` | `ministral-14b-latest` | Model served by that endpoint. |
| `DATABASE_URL` | `sqlite:///./mathutrice.db` | SQLite locally; PostgreSQL when deployed. |
| `SESSION_SECRET` | placeholder | Signs session cookies. See [the caveat below](#session_secret-caveat). |
| `AUTH_MODE` | `dev` in `.env.example`; `entra` when unset | `dev` or `entra`. See [Authentication](#authentication). |
| `DEV_LOGIN_KEY` | _empty_ | Optional shared key for the dev sign-in. |
| `CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID` | commented out | Microsoft Entra ID app registration. Required when `AUTH_MODE=entra`. |
| `REDIRECT_URL`, `POST_LOGOUT_REDIRECT_URL` | commented out | Entra redirects after sign-in and sign-out. Required when `AUTH_MODE=entra`. |

To use another LLM endpoint, change `LLM_BASE_URL`, `LLM_MODEL` and `LLM_API_KEY` together.

## Authentication

Two modes, chosen by `AUTH_MODE`:

- **`entra`** (the default when `AUTH_MODE` is unset): users sign in through Microsoft Entra ID. Requires `CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`, `REDIRECT_URL` and `POST_LOGOUT_REDIRECT_URL`.
- **`dev`**: the **connexion de développement**. No identity provider: you pick an email address and a role (Student, Teacher or Admin) and are signed in as that user, **with no proof of identity**. It exists so forks and local clones run without Entra credentials. The `/dev/login` routes only exist in this mode, and a red banner shows on every page.

### Dev sign-in

Open `/` while signed out and you are redirected to `/dev/login`. The email must end in `@epfedu.fr` or `@epf.fr`. A user that does not exist yet is created; with no role given, they are a Student. Teachers and Admins land on `/teacher`, students on `/`.

Set `DEV_LOGIN_KEY` to require a shared key on the sign-in form. It is ignored when `AUTH_MODE=entra`.

#### Scripted sign-in

`POST /dev/login` takes form fields `email` (required), `role` (`student`, `teacher` or `admin`), `name` and `key` (required when `DEV_LOGIN_KEY` is set). Keep the session cookie between requests with a cookie jar:

```sh
# Sign in as a teacher and store the session cookie
curl -s -c cookies.txt \
  -d 'email=prof@epfedu.fr' -d 'role=teacher' -d 'key=<DEV_LOGIN_KEY>' \
  http://localhost:8000/dev/login

# Reuse it on later requests
curl -s -b cookies.txt http://localhost:8000/teacher
```

Omit `key` when `DEV_LOGIN_KEY` is empty. A successful sign-in answers `303`; a wrong key answers `401`, a non-EPF address `403` and an unknown role `400`. Sessions last one hour.

### `SESSION_SECRET` caveat

The session cookie is signed with `SESSION_SECRET`. With the placeholder value from `.env.example`, **anyone can forge a valid session cookie** and sign in as any user, skipping `DEV_LOGIN_KEY` entirely. Set a random secret (for example `openssl rand -hex 32`) on any environment reachable by other people.

## Deployment checklist

- [ ] `AUTH_MODE` non défini ou `entra`. Never `dev`: it signs anyone in as anyone.
- [ ] `SESSION_SECRET` replaced by a random secret.
- [ ] Entra settings (`CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`, `REDIRECT_URL`, `POST_LOGOUT_REDIRECT_URL`) set.
- [ ] `DATABASE_URL` pointing at PostgreSQL.
- [ ] `LLM_API_KEY` set. On Mistral's free plan, requests may be used for training: for real student data, turn that off in the admin panel under Privacy.

## Contributing

Package boundaries are machine-checked: read [`mathutrice/README.md`](mathutrice/README.md) before adding a package or importing across one, then run:

```sh
uv run tach check
uv run python scripts/check_cycles.py
```
