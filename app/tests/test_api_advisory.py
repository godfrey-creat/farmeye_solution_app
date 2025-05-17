import unittest
from flask import current_app
from app import create_app, db
from app.auth.models import User

class AdvisoryApiTestCase(unittest.TestCase):
    def setUp(self):
        # Set up test app and client
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        # Set up test database
        db.create_all()
        # Create a test user
        self.password = 'test1234'
        user = User(
            email='testuser@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            is_approved=True
        )
        user.verify_password(self.password)
        db.session.add(user)
        db.session.commit()
        self.user = user

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self):
        # Adjust as needed for your login endpoint/logic
        return self.client.post('/login', data={
            'email': self.user.email,
            'password': self.password
        }, follow_redirects=True)

    def test_dashboard_advisory_appears(self):
        # First, login the user
        self.login()
        # Now request the dashboard data
        response = self.client.get('/api/dashboard-data')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('recommendations', data)
        advisories = data['recommendations']
        self.assertIsInstance(advisories, list)
        # You can check that at least one advisory contains the expected keys
        found = False
        for advisory in advisories:
            if all(k in advisory for k in ['action', 'description', 'due', 'priority']):
                found = True
                break
        self.assertTrue(found, "No advisory with expected fields found in recommendations")

if __name__ == '__main__':
    unittest.main()