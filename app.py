import json
import os
import secrets
from hmac import compare_digest
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to view your private health information."
login_manager.login_message_category = "info"

MOODS = ("Happy", "Normal", "Sad", "Angry", "Stressed")


def _utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    health_logs = db.relationship("HealthLog", backref="user", lazy=True, cascade="all, delete-orphan")
    journal_entries = db.relationship("JournalEntry", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class HealthLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    log_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    mood = db.Column(db.String(20), nullable=False, default="Normal")
    feelings_note = db.Column(db.String(500), default="")
    sleep_hours = db.Column(db.Float, default=0)
    water_glasses = db.Column(db.Integer, default=0)
    energy_level = db.Column(db.Integer, default=3)
    symptoms = db.Column(db.String(500), default="")
    exercise_minutes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "log_date", name="unique_user_daily_log"),)


class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    entry_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def seed_user_sample_data(user_id):
    existing_count = HealthLog.query.filter_by(user_id=user_id).count()
    if existing_count > 0:
        return

    today = date.today()
    sample_pattern = [
        (29, "Normal", 7.0, 6, 3, 20, "Getting back into routine", ""),
        (28, "Happy", 8.0, 7, 4, 35, "Sunny day, felt very energized", ""),
        (27, "Happy", 7.5, 8, 4, 30, "Good focus at work", ""),
        (26, "Normal", 7.0, 6, 3, 15, "Standard day, took an evening walk", ""),
        (25, "Stressed", 5.5, 5, 2, 10, "Busy deadlines, worked late", "Tight shoulders"),
        (24, "Sad", 6.0, 5, 2, 0, "Felt fatigued and low motivation", "Mild headache"),
        (23, "Normal", 7.5, 7, 3, 25, "Restful evening, starting to bounce back", ""),
        (22, "Happy", 8.0, 8, 4, 40, "Went for an outdoor bike ride", ""),
        (21, "Happy", 8.5, 8, 5, 45, "Weekend recharge with friends", ""),
        (20, "Normal", 7.0, 7, 3, 20, "Cooked healthy dinner", ""),
        (19, "Normal", 7.0, 6, 3, 20, "Quiet productive day", ""),
        (18, "Stressed", 6.0, 5, 2, 15, "Long meetings all day", "Eye strain"),
        (17, "Normal", 7.0, 6, 3, 25, "Early bedtime helped", ""),
        (16, "Happy", 7.5, 8, 4, 30, "Accomplished a key milestone", ""),
        (15, "Happy", 8.0, 7, 4, 35, "Feeling grateful and calm", ""),
        (14, "Normal", 7.0, 7, 3, 20, "Consistent habit check-in", ""),
        (13, "Normal", 7.5, 6, 3, 25, "Mid-week consistency", ""),
        (12, "Angry", 5.5, 5, 2, 15, "Frustrating delays and commute", "Tension in neck"),
        (11, "Normal", 7.0, 7, 3, 30, "Took time to decompress and breathe", ""),
        (10, "Happy", 8.0, 8, 4, 35, "Great gym workout", ""),
        (9, "Happy", 7.5, 8, 4, 25, "Clear headspace", ""),
        (8, "Normal", 7.0, 7, 3, 20, "Steady progress", ""),
        (7, "Normal", 6.5, 6, 3, 20, "Slightly shorter sleep", ""),
        (6, "Stressed", 6.0, 5, 2, 10, "A lot on my plate today", "Mild headache"),
        (5, "Sad", 6.5, 6, 2, 0, "Gloomy weather and felt drained", ""),
        (4, "Normal", 7.5, 7, 3, 25, "Reset evening with tea and reading", ""),
        (3, "Happy", 8.0, 8, 4, 35, "Energizing run in the park", ""),
        (2, "Happy", 7.5, 8, 4, 30, "Good rhythm and connection with family", ""),
        (1, "Normal", 7.0, 7, 3, 25, "Relaxed Sunday afternoon", ""),
        (0, "Happy", 7.5, 8, 4, 35, "Feeling centered and ready for the day ahead", ""),
    ]

    for offset, mood, sleep, water, energy, exercise, note, symptoms in sample_pattern:
        log_date = today - timedelta(days=offset)
        log = HealthLog(
            user_id=user_id,
            log_date=log_date,
            mood=mood,
            feelings_note=note,
            sleep_hours=sleep,
            water_glasses=water,
            energy_level=energy,
            exercise_minutes=exercise,
            symptoms=symptoms,
        )
        db.session.add(log)

    journals = [
        (today - timedelta(days=21), "Finding my morning stride", "Woke up without snoozing. Did 10 minutes of gentle stretching followed by hydration. Amazing how taking just 15 minutes before touching my phone changes the entire tone of the morning."),
        (today - timedelta(days=14), "The link between boundaries and calm", "Saying no to extra evening commitments felt uncomfortable, but I actually got 8 hours of sleep and felt present with myself. Peace of mind is a habit of small daily decisions."),
        (today - timedelta(days=7), "Recovering from high-stress days", "Noticeable tension when deadlines piled up. What helped was turning off notifications after 8 PM, drinking plenty of water, and having a warm shower. Health is about bouncing back, not being perfect every day."),
        (today, "Reflections on steady wellbeing", "Looking back across the past month of check-ins, the pattern is unmistakable: hydration and 7+ hours of sleep directly anchor my mood and energy. Excited to keep this momentum going!"),
    ]
    for entry_date, title, body in journals:
        db.session.add(JournalEntry(
            user_id=user_id,
            entry_date=entry_date,
            title=title,
            body=body,
        ))

    db.session.commit()


def seed_demo_account():
    demo_email = "demo@healthmood.com"
    user = User.query.filter_by(email=demo_email).first()
    if not user:
        user = User(name="Alex Rivera", email=demo_email)
        user.set_password("demo12345")
        db.session.add(user)
        db.session.commit()
    seed_user_sample_data(user.id)
    return user


def create_app(test_config=None):
    app = Flask(__name__)
    database_url = os.getenv("DATABASE_URL", "sqlite:///healthmood.db")
    if database_url.startswith("mysql://"):
        database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "change-this-secret-before-deploying"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    @app.context_processor
    def csrf_context():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return {"csrf_token": session["csrf_token"]}

    @app.before_request
    def protect_post_requests():
        if app.config["TESTING"] or request.method != "POST":
            return
        submitted_token = request.form.get("csrf_token", "")
        expected_token = session.get("csrf_token", "")
        if not expected_token or not submitted_token or not compare_digest(submitted_token, expected_token):
            abort(400)
    with app.app_context():
        db.create_all()
        if not app.config.get("TESTING"):
            try:
                seed_demo_account()
            except Exception:
                pass

    @app.route("/")
    def index():
        return redirect(url_for("dashboard" if current_user.is_authenticated else "login"))

    @app.route("/demo")
    @app.route("/demo-login", methods=["GET", "POST"])
    def demo_login():
        user = seed_demo_account()
        login_user(user)
        flash("Welcome to HealthMood! You are viewing the live demo account with preloaded 30-day health analytics and reflections.", "success")
        return redirect(url_for("dashboard"))

    @app.post("/seed-sample-data")
    @login_required
    def load_sample_data():
        seed_user_sample_data(current_user.id)
        flash("Sample check-ins and journal reflections have been added to your account.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not name or not email or not password:
                flash("Name, email, and password are required.", "error")
            elif len(password) < 8:
                flash("Use a password with at least 8 characters.", "error")
            elif User.query.filter_by(email=email).first():
                flash("An account with that email already exists. Please sign in.", "error")
            else:
                user = User(name=name, email=email)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash("Welcome to HealthMood. Your private dashboard is ready.", "success")
                return redirect(url_for("dashboard"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(request.form.get("password", "")):
                login_user(user, remember=bool(request.form.get("remember")))
                next_page = request.args.get("next")
                return redirect(next_page if _is_safe_next_url(next_page) else url_for("dashboard"))
            flash("Email or password was not recognised.", "error")
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been signed out.", "info")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        today_log = _user_log_for_date(current_user.id, date.today())
        recent_logs = (
            HealthLog.query.filter_by(user_id=current_user.id)
            .order_by(HealthLog.log_date.desc()).limit(7).all()
        )
        return render_template(
            "dashboard.html",
            today_log=today_log,
            recent_logs=recent_logs,
            suggestions=wellness_suggestions(recent_logs),
            mood_icons=mood_icons(),
        )

    @app.route("/track", methods=["GET", "POST"])
    @login_required
    def track():
        try:
            selected_date = _parse_date(request.values.get("date"))
        except ValueError as error:
            flash(str(error), "error")
            selected_date = date.today()
        health_log = _user_log_for_date(current_user.id, selected_date)
        if request.method == "POST":
            try:
                mood = request.form.get("mood", "Normal")
                if mood not in MOODS:
                    raise ValueError("Please select a valid mood.")
                sleep_hours = _bounded_float(request.form.get("sleep_hours"), 0, 24, "Sleep")
                water_glasses = _bounded_int(request.form.get("water_glasses"), 0, 50, "Water intake")
                energy_level = _bounded_int(request.form.get("energy_level"), 1, 5, "Energy level")
                exercise_minutes = _bounded_int(request.form.get("exercise_minutes"), 0, 1440, "Exercise")
                if not health_log:
                    health_log = HealthLog(user_id=current_user.id, log_date=selected_date)
                    db.session.add(health_log)
                health_log.mood = mood
                health_log.feelings_note = request.form.get("feelings_note", "").strip()[:500]
                health_log.sleep_hours = sleep_hours
                health_log.water_glasses = water_glasses
                health_log.energy_level = energy_level
                health_log.symptoms = request.form.get("symptoms", "").strip()[:500]
                health_log.exercise_minutes = exercise_minutes
                db.session.commit()
                flash("Your daily check-in has been saved.", "success")
                return redirect(url_for("dashboard"))
            except ValueError as error:
                flash(str(error), "error")
        return render_template("track.html", health_log=health_log, selected_date=selected_date, moods=MOODS)

    @app.route("/journal", methods=["GET", "POST"])
    @login_required
    def journal():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            body = request.form.get("body", "").strip()
            if not title or not body:
                flash("A title and your journal entry are required.", "error")
            else:
                try:
                    entry_date = _parse_date(request.form.get("entry_date"))
                except ValueError as error:
                    flash(str(error), "error")
                else:
                    entry = JournalEntry(
                        user_id=current_user.id, entry_date=entry_date,
                        title=title[:160], body=body,
                    )
                    db.session.add(entry)
                    db.session.commit()
                    flash("Journal entry saved.", "success")
                    return redirect(url_for("journal"))
        entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc()).all()
        return render_template("journal.html", entries=entries, today=date.today())

    @app.route("/journal/<int:entry_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_journal(entry_id):
        entry = _owned_journal_entry(entry_id)
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            body = request.form.get("body", "").strip()
            if not title or not body:
                flash("A title and your journal entry are required.", "error")
            else:
                try:
                    entry_date = _parse_date(request.form.get("entry_date"))
                except ValueError as error:
                    flash(str(error), "error")
                else:
                    entry.title = title[:160]
                    entry.body = body
                    entry.entry_date = entry_date
                    db.session.commit()
                    flash("Journal entry updated.", "success")
                    return redirect(url_for("journal"))
        return render_template("journal_form.html", entry=entry, today=date.today())

    @app.post("/journal/<int:entry_id>/delete")
    @login_required
    def delete_journal(entry_id):
        entry = _owned_journal_entry(entry_id)
        db.session.delete(entry)
        db.session.commit()
        flash("Journal entry deleted.", "info")
        return redirect(url_for("journal"))

    @app.route("/analytics")
    @login_required
    def analytics():
        days = 30
        start_date = date.today() - timedelta(days=days - 1)
        logs = (HealthLog.query.filter(HealthLog.user_id == current_user.id, HealthLog.log_date >= start_date)
                .order_by(HealthLog.log_date.asc()).all())
        chart_data = chart_payload(logs, days)
        return render_template(
            "analytics.html", chart_data=json.dumps(chart_data),
            chart_rows=chart_rows(logs, 30), suggestions=wellness_suggestions(logs), summary=summary_stats(logs),
        )

    return app


def _parse_date(value):
    if not value:
        return date.today()
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Please use a valid date.")
    if parsed > date.today():
        raise ValueError("You cannot add a health record for a future date.")
    return parsed


def _is_safe_next_url(target):
    if not target:
        return False
    host = urlparse(request.host_url)
    candidate = urlparse(urljoin(request.host_url, target))
    return candidate.scheme in ("http", "https") and candidate.netloc == host.netloc


def _bounded_float(value, minimum, maximum, label):
    try:
        number = float(value or 0)
    except ValueError:
        raise ValueError(f"{label} must be a number.")
    if not minimum <= number <= maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}.")
    return number


def _bounded_int(value, minimum, maximum, label):
    try:
        number = int(value or 0)
    except ValueError:
        raise ValueError(f"{label} must be a whole number.")
    if not minimum <= number <= maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}.")
    return number


def _user_log_for_date(user_id, log_date):
    return HealthLog.query.filter_by(user_id=user_id, log_date=log_date).first()


def _owned_journal_entry(entry_id):
    entry = db.session.get(JournalEntry, entry_id)
    if not entry or entry.user_id != current_user.id:
        abort(404)
    return entry


def mood_icons():
    return {"Happy": "☀", "Normal": "●", "Sad": "☁", "Angry": "⚡", "Stressed": "◌"}


def summary_stats(logs):
    if not logs:
        return {"days": 0, "sleep": 0, "water": 0, "energy": 0}
    count = len(logs)
    return {
        "days": count,
        "sleep": round(sum(log.sleep_hours for log in logs) / count, 1),
        "water": round(sum(log.water_glasses for log in logs) / count, 1),
        "energy": round(sum(log.energy_level for log in logs) / count, 1),
    }


def wellness_suggestions(logs):
    if not logs:
        return ["Start with a quick daily check-in. Small, consistent notes make patterns easier to notice."]
    suggestions = []
    stats = summary_stats(logs)
    if stats["sleep"] < 7:
        suggestions.append("Your recent sleep average is below 7 hours. A regular wind-down and wake time may help support rest.")
    if stats["water"] < 6:
        suggestions.append("Your recorded water intake is below 6 glasses a day. Keeping water nearby can make regular sips easier.")
    if stats["energy"] < 3:
        suggestions.append("Your energy has been on the lower side. Consider gentle movement, a regular meal, or a short rest when possible.")
    if all(log.exercise_minutes < 20 for log in logs[-3:]):
        suggestions.append("You have logged little recent movement. Even a brief walk or stretch can be a manageable reset.")
    difficult_moods = [log for log in logs if log.mood in ("Sad", "Angry", "Stressed")]
    symptomatic = [log for log in difficult_moods if log.symptoms.strip()]
    if len(symptomatic) >= 2:
        suggestions.append("Some lower-mood check-ins also mention symptoms. Keep observing the pattern and consider speaking with a qualified professional if it concerns you.")
    if not suggestions:
        suggestions.append("Your recent check-ins look fairly balanced. Continue recording consistently to learn what helps you feel your best.")
    return suggestions[:3]


def chart_payload(logs, days):
    by_date = {log.log_date: log for log in logs}
    ordered_dates = [date.today() - timedelta(days=days - 1 - offset) for offset in range(days)]
    mood_values = {"Happy": 5, "Normal": 4, "Sad": 2, "Angry": 1, "Stressed": 1}
    return {
        "labels": [value.strftime("%b %d") for value in ordered_dates],
        "mood": [mood_values.get(by_date[value].mood) if value in by_date else None for value in ordered_dates],
        "sleep": [by_date[value].sleep_hours if value in by_date else None for value in ordered_dates],
        "energy": [by_date[value].energy_level if value in by_date else None for value in ordered_dates],
        "water": [by_date[value].water_glasses if value in by_date else None for value in ordered_dates],
    }


def chart_rows(logs, days):
    by_date = {log.log_date: log for log in logs}
    rows = []
    for offset in range(days - 1, -1, -1):
        value = date.today() - timedelta(days=offset)
        log = by_date.get(value)
        rows.append({
            "label": value.strftime("%a"),
            "date": value.strftime("%b %d"),
            "mood": {"Happy": 5, "Normal": 4, "Sad": 2, "Angry": 1, "Stressed": 1}.get(log.mood, 0) if log else 0,
            "energy": log.energy_level if log else 0,
            "sleep": min(log.sleep_hours, 10) if log else 0,
            "water": min(log.water_glasses, 10) if log else 0,
        })
    return rows


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
