import unittest
from app import app, db
from app.models import User, Candidate, Employer, Job, CV, Application, UserRole


class TestApplicationAPI(unittest.TestCase):
    def setUp(self):
        # Khởi tạo app context
        self.app_context = app.app_context()
        self.app_context.push()

        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
        app.config['TESTING'] = True

        # Tạo client Flask
        self.client = app.test_client()

        # Reset DB
        db.drop_all()
        db.create_all()

        # Tạo user candidate
        candidate_user = User(username="cand1", role=UserRole.CANDIDATE)
        candidate_user.set_password("123")
        db.session.add(candidate_user)
        db.session.commit()

        self.candidate = Candidate(
            user_id=candidate_user.id,
            full_name="Nguyen Van A",
            email="a@example.com",
            phone="0123456789"
        )
        db.session.add(self.candidate)

        # Tạo CV cho candidate
        self.cv = CV(title="Backend CV", skills="Python, Flask", experience="1 year", education="Bachelor")
        self.cv.candidate = self.candidate
        db.session.add(self.cv)

        # Tạo employer user
        employer_user = User(username="emp1", role=UserRole.EMPLOYER)
        employer_user.set_password("123")
        db.session.add(employer_user)
        db.session.commit()

        self.employer = Employer(
            user_id=employer_user.id,
            company_name="ABC Corp"
        )
        db.session.add(self.employer)

        # Tạo Job
        self.job = Job(
            employer=self.employer,
            title="Flask Developer",
            description="Develop API",
            requirements="Python, Flask",
            location="HCM",
            salary=1000,
            status="active"
        )
        db.session.add(self.job)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_apply_and_review(self):
        # 🔹 Ứng viên apply job
        with self.client.session_transaction() as sess:
            sess['user_type'] = 'candidate'
            sess['_user_id'] = str(self.candidate.user_id)  # giả lập login

        res = self.client.post(
            "/api/apply",
            json={"job_id": self.job.id, "cv_id": self.cv.id}
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("application_id", data)

        app_id = data["application_id"]

        # 🔹 Employer review application
        with self.client.session_transaction() as sess:
            sess['user_type'] = 'employer'
            sess['_user_id'] = str(self.employer.user_id)  # giả lập login

        res2 = self.client.put(
            f"/api/application/{app_id}/review",
            json={"status": "accepted"}
        )
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertIn("Hồ sơ đã cập nhật sang trạng thái accepted", data2["message"])


if __name__ == "__main__":
    unittest.main()
