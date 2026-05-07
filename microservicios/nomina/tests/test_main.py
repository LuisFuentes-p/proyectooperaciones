import unittest

from fastapi.testclient import TestClient

import app.main as nomina_app


class NominaServiceTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(nomina_app.app)

    def tearDown(self):
        self.client.close()

    def test_health_and_payroll(self):
        health_response = self.client.get("/health")
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(health_response.json()["service"], "nomina")

        payroll_response = self.client.get("/payroll")
        self.assertEqual(payroll_response.status_code, 200)
        message = payroll_response.json()["message"].lower()
        self.assertTrue("nómina" in message or "nomina" in message)
