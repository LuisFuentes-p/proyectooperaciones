from fastapi.testclient import TestClient

import app.main as nomina_app


def test_health_and_payroll():
    with TestClient(nomina_app.app) as client:
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["service"] == "nomina"

        payroll_response = client.get("/payroll")
        assert payroll_response.status_code == 200
        assert "nómina" in payroll_response.json()["message"].lower() or "nomina" in payroll_response.json()["message"].lower()
