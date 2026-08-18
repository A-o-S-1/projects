# Deployment Checklist — Mater Domini Schools Website

This is a practical, in-order checklist for taking Phase 1 (the public
website) from your machine to a live production server. Work through it
top to bottom the first time you deploy; keep it handy for future
redeploys too.

## 1. Choose where it will run

Any of these work with zero code changes, since settings are already
environment-driven (`config/settings/prod.py`):

- A VPS you manage yourself (DigitalOcean, Linode, a Nigerian host) running Gunicorn behind Nginx
- A PaaS (Railway, Render, PythonAnywhere) that handles the server for you

If you're unsure, a PaaS is the least maintenance for a small school site.

## 2. Get a Postgres database

Production uses PostgreSQL, not the SQLite file you've been developing
with (SQLite is fine for one developer on one laptop; it is not safe for
a live site with concurrent users). Most hosts above offer a Postgres
add-on. You'll get a `DATABASE_URL` connection string from whichever
host you choose — keep it, you need it in step 4.

## 3. Buy/point the domain

Point `materdominischool.com.ng` (and `www.` if you use it) at your
server or hosting platform's IP/CNAME, per your host's instructions.
This can take a few hours to propagate — do it early.

## 4. Set environment variables

None of these live in code — set them on your server or hosting
platform's dashboard:

| Variable | Value |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
| `DJANGO_SECRET_KEY` | A long random string — **generate a fresh one**, don't reuse the dev one. Run: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG` | `False` (or leave unset — False is the default) |
| `DJANGO_ALLOWED_HOSTS` | `materdominischool.com.ng,www.materdominischool.com.ng` |
| `DATABASE_URL` | The Postgres connection string from step 2 |

`.env.example` in the repo shows this same list — copy it as a starting
point, never commit the real filled-in version.

## 5. Install dependencies and run migrations

```bash
pip install -r requirements/prod.txt
python manage.py migrate
python manage.py createsuperuser
```

Then load starter content (real school info + placeholder demo entries
you'll replace via `/admin/`):

```bash
python manage.py seed_demo_data
```

## 6. Collect static files

**This step is easy to forget and the site will look broken without it**
(unstyled HTML, no logo) — WhiteNoise requires a build manifest that only
`collectstatic` generates:

```bash
python manage.py collectstatic --noinput
```

Re-run this every time you deploy new CSS/JS/image changes.

## 7. Run with Gunicorn (if self-hosting, not using a PaaS)

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Put Nginx in front of it as a reverse proxy + HTTPS terminator. A
minimal Nginx config:

```nginx
server {
    listen 80;
    server_name materdominischool.com.ng www.materdominischool.com.ng;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name materdominischool.com.ng www.materdominischool.com.ng;

    ssl_certificate     /etc/letsencrypt/live/materdominischool.com.ng/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/materdominischool.com.ng/privkey.pem;

    location /static/ {
        alias /path/to/school_project/staticfiles/;
    }
    location /media/ {
        alias /path/to/school_project/media/;
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Use [Certbot](https://certbot.eff.org/) for a free Let's Encrypt
certificate. `SECURE_SSL_REDIRECT` and friends are already turned on in
`prod.py`, so once HTTPS is live, HTTP will auto-redirect.

## 8. Verify before telling anyone the site is live

- [ ] Visit every page: `/`, `/about/`, `/academics/`, `/admissions/`, `/staff/`, `/management/`, `/gallery/`, `/news/`, `/events/`, `/contact/`
- [ ] Submit the Admissions inquiry form and the Contact form — confirm both save (check `/admin/`)
- [ ] Log into `/admin/` and replace every `[Placeholder ...]` entry (staff bios, sample news/events) with real content — search the admin for `[Placeholder` and `[Sample` to find every one
- [ ] Upload the school's real photos in Gallery, staff photos in Staff Directory
- [ ] Confirm HTTPS works and HTTP redirects to it
- [ ] Confirm `/admin/` requires login and isn't publicly browsable
- [ ] Check the site on an actual phone, not just a resized browser window
- [ ] Visit a nonsense URL (e.g. `/asdf/`) and confirm the custom "Page Not Found" page shows, not a raw Django error
- [ ] Check `/sitemap.xml` and `/robots.txt` both load and list the real domain (not `127.0.0.1`)
- [ ] Run `python manage.py check --deploy` against your production settings — it should report zero issues; if anything shows up, fix it before announcing the site is live

## 9. Ongoing maintenance

- **Backups**: set up automatic daily Postgres backups through your host — this is more important than almost anything else on this list. Losing the database means losing every result, staff profile, and news post.
- **Updating content**: school staff can add News/Events/Gallery photos/Staff entries anytime via `/admin/` — no developer needed for routine content updates.
- **Deploying code changes**: pull the latest code, `pip install -r requirements/prod.txt` (in case dependencies changed), `python manage.py migrate` (in case models changed), `python manage.py collectstatic --noinput`, restart Gunicorn.
- **Rotating the SECRET_KEY**: only if you suspect it's been exposed — rotating it invalidates all active sessions (everyone gets logged out) but not stored data.
