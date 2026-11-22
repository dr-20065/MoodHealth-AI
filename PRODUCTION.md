# Public deployment checklist

This project is configured for a small public demo on Render through `render.yaml`. It uses a managed PostgreSQL database in production, while preserving MySQL support through `DATABASE_URL` for environments where MySQL is required.

## Before sharing a public URL

- Set a unique, long `SECRET_KEY`; Render generates one when deploying from this repository configuration.
- Keep `SESSION_COOKIE_SECURE=true` and serve only over HTTPS.
- Use a managed database and take regular backups; do not deploy with the local SQLite fallback.
- Publish a privacy notice and terms appropriate to your location and audience.
- Treat this as a wellbeing demo until it has email verification, password-reset flows, rate limiting, monitoring, backups, and a security review.

## Important health-data note

The current application is **not** represented as HIPAA-, GDPR-, or medical-device compliant. Do not invite users to enter sensitive real health information until legal, privacy, security, retention, and hosting requirements have been reviewed for the intended audience.
