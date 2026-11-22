# HealthMood

HealthMood is a private mood and physical health tracker built with Flask. It helps people keep brief daily check-ins, preserve health journal entries, notice wellbeing patterns, and receive gentle, habit-focused observations without medical diagnosis.

## Instant demo preview

Anyone opening this project can view a fully functioning product with preloaded 30-day health analytics, logs, and journal reflections:

- **1-Click Launch (Windows):** Double-click `run.bat` or run `.\run.bat` in PowerShell. It sets up the environment and opens the demo in your browser.
- **Instant Demo URL:** Visit `http://127.0.0.1:5000/demo` (or click **"✨ Explore Live Demo"** on the sign-in page).
- **Preloaded Demo Credentials:**
  - **Email:** `demo@healthmood.com`
  - **Password:** `demo12345`
- **Sample Data for Any Account:** If you prefer to register your own account, you can click **"⚡ Load sample data"** directly from the empty dashboard or insights screen to preview full charts and trends immediately.

## Included modules

- **Authentication & Privacy:** Account registration, hashed-password login, logout, CSRF protection, and private per-user records.
- **Daily Mood Check-ins:** Track Happy, Normal, Sad, Angry, and Stressed ratings, plus optional contextual notes.
- **Physical Health Tracking:** Sleep duration, hydration (glasses of water), energy levels (1–5 scale), exercise minutes, and physical symptom logs.
- **Health Reflections Journal:** Dated journal entries that can be written, reviewed, edited, and deleted.
- **30-Day Health Analytics:** Local, server-rendered visual trend charts for mood vs. energy, and sleep vs. hydration with 30-day summary averages.
- **Wellness Observations:** Personalized, non-diagnostic habit reflections generated from recent check-ins.

## Run locally

### Quick start (Windows)
Double-click `run.bat` or execute in terminal:
```cmd
run.bat
```

### Manual setup

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` (optional for local SQLite development):

   ```powershell
   copy .env.example .env
   ```

4. Start the application:

   ```powershell
   py app.py
   # or
   flask --app app run --debug
   ```

5. Visit `http://127.0.0.1:5000` or `http://127.0.0.1:5000/demo`.

## Database configuration

By default, HealthMood uses SQLite for seamless local development and immediate zero-config testing.

To connect to MySQL or PostgreSQL (e.g., in production):
```dotenv
DATABASE_URL=mysql+pymysql://username:password@localhost/healthmood
# or
DATABASE_URL=postgresql+psycopg://username:password@localhost/healthmood
SECRET_KEY=your-secure-random-secret
SESSION_COOKIE_SECURE=true
```

## Running tests

Run the test suite to verify all routes, privacy constraints, and demo flows:

```powershell
py -m unittest test_app.py
```

## Privacy and safety notes

- Every health log and journal route is authenticated and queries the current user’s own records only.
- Passwords are stored as Werkzeug password hashes, never plaintext.
- Wellness notes are general habits-based observations—not medical advice, diagnosis, or treatment.
