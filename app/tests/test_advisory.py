import unittest

from app.utils.advisory import generate_ten_day_advisory

class TestAdvisoryGeneration(unittest.TestCase):
    def setUp(self):
        # Example mock data
        self.soil_moisture_data = {
            "recent_readings": [65, 66, 67, 62, 60, 58, 75, 72, 68, 65],
            "current": 65,
            "last_irrigation": "2 days ago",
            "next_irrigation": "Tomorrow"
        }
        self.weather_summary = {
            "temperature": 25,
            "condition": "Partly Cloudy",
            "icon": "02d",
            "forecast": "Light rain expected in 36 hours"
        }
        self.satellite_data = {
            "ndvi": [0.62, 0.65, 0.60, 0.66, 0.64],
            "analysis": "Vegetation vigor is moderate to high"
        }
        self.model_prediction_data = {
            "yield_forecast": "Expected yield is 85% of maximum.",
            "pest_risk": "Medium risk of corn earworm in next 10 days"
        }

    def test_generate_advisory(self):
        advisory = generate_ten_day_advisory(
            soil_moisture=self.soil_moisture_data,
            weather=self.weather_summary,
            satellite=self.satellite_data,
            model_prediction=self.model_prediction_data
        )
        # Check output is a dictionary
        self.assertIsInstance(advisory, dict)
        # Check required keys
        for key in ["action", "description", "due", "priority"]:
            self.assertIn(key, advisory)
        # Optionally check that the values are not empty
        self.assertTrue(advisory["action"])
        self.assertTrue(advisory["description"])
        self.assertTrue(advisory["due"])
        self.assertTrue(advisory["priority"])

if __name__ == "__main__":
    unittest.main()