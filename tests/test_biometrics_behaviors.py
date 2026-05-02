import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from services import biometrics  # noqa: E402


class BiometricsBehaviorTests(unittest.TestCase):
    def tearDown(self):
        for key in (
            "BIOMETRIC_MODE",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_REGION",
        ):
            os.environ.pop(key, None)

    def test_bypass_mode_is_explicit_and_auditable(self):
        os.environ["BIOMETRIC_MODE"] = "bypass"

        result = biometrics.verify_face("YWJj", "employee-1")

        self.assertEqual(result["match"], True)
        self.assertEqual(result["status"], "bypassed")
        self.assertEqual(result["provider"], "local_bypass")

    def test_missing_mode_does_not_implicitly_bypass(self):
        result = biometrics.verify_face("YWJj", "employee-1")

        self.assertEqual(result["match"], False)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["provider"], "aws_rekognition")

    def test_aws_mode_does_not_pass_without_enrolled_face(self):
        os.environ["BIOMETRIC_MODE"] = "aws"
        os.environ["AWS_ACCESS_KEY_ID"] = "fake-key"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "fake-secret"
        os.environ["AWS_REKOGNITION_COLLECTION_ID"] = "employees"

        with patch.object(biometrics, "query_one", return_value={"face_id_aws": None}, create=True):
            result = biometrics.verify_face("YWJj", "employee-1")

        self.assertEqual(result["match"], False)
        self.assertEqual(result["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
