# app/route/model.py
from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64
import json
import os

model_router = APIRouter(prefix="/model", tags=["model"])

def _b64url_cf(raw: bytes) -> str:
    """
    CloudFront 규칙에 맞춘 base64-url 변형
    (+ → -, = → _, / → ~)
    """
    s = base64.b64encode(raw).decode("utf-8")
    return s.replace("+", "-").replace("=", "_").replace("/", "~")

def _load_private_key(path: str):
    try:
        with open(path, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Private key load failed: {e}")

@model_router.get("/url")
async def get_model_signed_url():
    KEY_ID = os.getenv("CLOUDFRONT_KEY_ID")
    PRIV_PATH = os.getenv("CLOUDFRONT_PRIVATE_KEY_PATH")
    DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")
    OBJECT_KEY = os.getenv("MODEL_OBJECT_KEY", "kogpt.Q3_K_M.gguf")
    EXPIRE_MINUTES = int(os.getenv("URL_EXPIRE_MINUTES", "60"))

    if not (KEY_ID and PRIV_PATH and DOMAIN):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing CLOUDFRONT_KEY_ID / CLOUDFRONT_PRIVATE_KEY_PATH / CLOUDFRONT_DOMAIN",
        )

    # 리소스 URL (정확한 경로)
    resource_url = f"https://{DOMAIN}/{OBJECT_KEY}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    epoch_exp = int(expires_at.timestamp())

    # Custom Policy 사용 (정확하고 명확함)
    policy = {
        "Statement": [
            {
                "Resource": resource_url,
                "Condition": {
                    "DateLessThan": {"AWS:EpochTime": epoch_exp}
                    # 필요하면 IP제한도 추가 가능:
                    # "IpAddress": {"AWS:SourceIp": "1.2.3.4/32"}
                },
            }
        ]
    }
    policy_bytes = json.dumps(policy, separators=(",", ":")).encode("utf-8")

    # RSA-SHA1 서명 (CloudFront 요구사항)
    private_key = _load_private_key(PRIV_PATH)
    try:
        signature = private_key.sign(
            policy_bytes,
            padding.PKCS1v15(),
            hashes.SHA1(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sign failed: {e}")

    params = {
        "Policy": _b64url_cf(policy_bytes),
        "Signature": _b64url_cf(signature),
        "Key-Pair-Id": KEY_ID,
    }
    signed_url = f"{resource_url}?{urlencode(params)}"
    return {"url": signed_url, "expires": epoch_exp}
