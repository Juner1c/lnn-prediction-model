import unittest
import os
from src.api.main import app
from fastapi.testclient import TestClient

class TestDeploymentAssets(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_dockerfile_exists(self):
        dockerfile = r"c:\Users\Jhonric Gorillo\Desktop\JHONRIC_FILES\OJT\LNN-Prediction-Model-Project\Dockerfile"
        self.assertTrue(os.path.exists(dockerfile))

    def test_docker_compose_exists(self):
        compose_file = r"c:\Users\Jhonric Gorillo\Desktop\JHONRIC_FILES\OJT\LNN-Prediction-Model-Project\docker-compose.yml"
        self.assertTrue(os.path.exists(compose_file))

    def test_ci_workflow_exists(self):
        ci_file = r"c:\Users\Jhonric Gorillo\Desktop\JHONRIC_FILES\OJT\LNN-Prediction-Model-Project\.github\workflows\ci.yml"
        self.assertTrue(os.path.exists(ci_file))

    def test_deploy_script_exists(self):
        deploy_script = r"c:\Users\Jhonric Gorillo\Desktop\JHONRIC_FILES\OJT\LNN-Prediction-Model-Project\scripts\deploy.py"
        self.assertTrue(os.path.exists(deploy_script))

    def test_fastapi_app_routes(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "healthy")

if __name__ == "__main__":
    unittest.main()
