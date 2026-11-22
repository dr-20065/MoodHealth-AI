import unittest
from datetime import date

from app import HealthLog, JournalEntry, User, create_app, db


class HealthMoodTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def register(self, email="test@example.com", password="password123"):
        return self.client.post("/register", data={
            "name": "Test User", "email": email, "password": password,
        }, follow_redirects=True)

    def test_registration_creates_a_password_hash(self):
        response = self.register()
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            user = User.query.filter_by(email="test@example.com").one()
            self.assertNotEqual(user.password_hash, "password123")
            self.assertTrue(user.check_password("password123"))

    def test_daily_checkin_is_private_to_the_current_user(self):
        self.register()
        response = self.client.post("/track", data={
            "date": date.today().isoformat(), "mood": "Happy", "feelings_note": "Feeling good",
            "sleep_hours": "8", "water_glasses": "7", "energy_level": "4",
            "exercise_minutes": "20", "symptoms": "",
        }, follow_redirects=True)
        self.assertIn(b"daily check-in has been saved", response.data)
        with self.app.app_context():
            self.assertEqual(HealthLog.query.count(), 1)
            self.assertEqual(HealthLog.query.one().mood, "Happy")

    def test_journal_edit_and_delete_require_ownership(self):
        self.register("owner@example.com")
        with self.app.app_context():
            owner = User.query.filter_by(email="owner@example.com").one()
            entry = JournalEntry(user_id=owner.id, title="Private", body="Only mine")
            db.session.add(entry)
            db.session.commit()
            entry_id = entry.id
        self.client.post("/logout")
        self.register("other@example.com")
        self.assertEqual(self.client.get(f"/journal/{entry_id}/edit").status_code, 404)
        self.assertEqual(self.client.post(f"/journal/{entry_id}/delete").status_code, 404)

    def test_demo_login_seeds_and_redirects_to_dashboard(self):
        response = self.client.get("/demo", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Alex", response.data)
        self.assertIn(b"Overview", response.data)
        with self.app.app_context():
            demo_user = User.query.filter_by(email="demo@healthmood.com").first()
            self.assertIsNotNone(demo_user)
            self.assertEqual(HealthLog.query.filter_by(user_id=demo_user.id).count(), 30)
            self.assertGreater(JournalEntry.query.filter_by(user_id=demo_user.id).count(), 0)

    def test_seed_sample_data_populates_empty_account(self):
        self.register("newuser@example.com")
        response = self.client.post("/seed-sample-data", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sample check-ins and journal reflections have been added", response.data)
        with self.app.app_context():
            user = User.query.filter_by(email="newuser@example.com").one()
            self.assertEqual(HealthLog.query.filter_by(user_id=user.id).count(), 30)
            self.assertGreater(JournalEntry.query.filter_by(user_id=user.id).count(), 0)


if __name__ == "__main__":
    unittest.main()
