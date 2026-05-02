import base64
import binascii
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from utils.db import query_one

def verify_face(photo_base64, employee_id):
    """
    Valida el rostro del empleado.

    BIOMETRIC_MODE=bypass permite desarrollo local y queda auditado como
    biometric_status=bypassed. BIOMETRIC_MODE=aws exige Rekognition real.
    """
    if not photo_base64:
        return {
            "match": False,
            "status": "unavailable",
            "confidence": 0,
            "error": "No se proporcionó imagen para validación"
        }

    mode = os.getenv("BIOMETRIC_MODE", "aws").strip().lower()
    if mode in ("bypass", "dev", "local", "disabled"):
        return {
            "match": True,
            "status": "bypassed",
            "confidence": 0.0,
            "provider": "local_bypass"
        }

    if mode not in ("aws", "rekognition", "strict"):
        return {
            "match": False,
            "status": "unavailable",
            "confidence": 0.0,
            "provider": "none",
            "error": f"BIOMETRIC_MODE no soportado: {mode}"
        }

    aws_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_REGION', 'us-east-1')
    collection_id = os.getenv('AWS_REKOGNITION_COLLECTION_ID') or os.getenv('BIOMETRIC_COLLECTION_ID')
    threshold = float(os.getenv('BIOMETRIC_FACE_THRESHOLD', '90'))

    if not aws_key or not aws_secret or not collection_id:
        print("[Biometrics] AWS Rekognition no configurado completamente.")
        return {
            "match": False,
            "status": "unavailable",
            "confidence": 0.0,
            "provider": "aws_rekognition"
        }

    employee = query_one(
        "SELECT face_id_aws FROM employees WHERE id = %s",
        (employee_id,)
    )
    enrolled_face_id = employee.get("face_id_aws") if employee else None
    if not enrolled_face_id:
        return {
            "match": False,
            "status": "unavailable",
            "confidence": 0.0,
            "provider": "aws_rekognition",
            "error": "Empleado sin face_id_aws enrolado"
        }

    try:
        if photo_base64.startswith("data:") and "," in photo_base64:
            photo_base64 = photo_base64.split(",", 1)[1]
        image_bytes = base64.b64decode(photo_base64, validate=True)

        client = boto3.client(
            'rekognition',
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name=region
        )

        response = client.search_faces_by_image(
            CollectionId=collection_id,
            Image={"Bytes": image_bytes},
            FaceMatchThreshold=threshold,
            MaxFaces=5,
        )

        matches = response.get("FaceMatches", [])
        matching_face = next(
            (
                match
                for match in matches
                if match.get("Face", {}).get("FaceId") == enrolled_face_id
            ),
            None
        )

        if not matching_face:
            confidence = max((m.get("Similarity", 0.0) for m in matches), default=0.0)
            return {
                "match": False,
                "status": "failed",
                "confidence": confidence,
                "provider": "aws_rekognition"
            }

        return {
            "match": True,
            "status": "passed",
            "confidence": matching_face.get("Similarity", 0.0),
            "provider": "aws_rekognition"
        }

    except (binascii.Error, ValueError) as e:
        return {
            "match": False,
            "status": "failed",
            "confidence": 0.0,
            "error": f"Imagen base64 invalida: {e}",
            "provider": "aws_rekognition"
        }
    except (BotoCoreError, ClientError, Exception) as e:
        print(f"[Biometrics] Error en validación AWS: {e}")
        return {
            "match": False,
            "status": "unavailable",
            "confidence": 0,
            "error": str(e),
            "provider": "aws_rekognition"
        }
