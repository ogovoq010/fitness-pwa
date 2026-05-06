import hashlib
import hmac
import json
import logging
import os
import urllib.parse
from typing import Any

import firebase_admin
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, firestore
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ── Firebase init ────────────────────────────────────────────────────────────
if not firebase_admin._apps:
    key_json = os.environ["FIREBASE_KEY_JSON"]
    cred = credentials.Certificate(json.loads(key_json))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ── App ──────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")  # напр. https://user.github.io

app = FastAPI(title="FitTrack API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN] if ALLOWED_ORIGIN != "*" else ["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Telegram auth ────────────────────────────────────────────────────────────
def _validate_init_data(init_data: str) -> dict:
    """Перевіряє підпис Telegram WebApp initData, повертає user dict."""
    try:
        params = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received_hash = params.pop("hash", "")

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(params.items())
        )
        secret_key = hmac.new(
            b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256
        ).digest()
        computed_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            raise HTTPException(status_code=401, detail="Невалідний підпис Telegram")

        user = json.loads(params.get("user", "{}"))
        if not user.get("id"):
            raise HTTPException(status_code=401, detail="Немає user.id")

        return user
    except HTTPException:
        raise
    except Exception as e:
        log.warning("Auth error: %s", e)
        raise HTTPException(status_code=401, detail="Помилка авторизації")


def get_user(x_init_data: str = Header(None, alias="X-Init-Data")) -> dict:
    if not x_init_data:
        raise HTTPException(status_code=401, detail="Відсутній заголовок X-Init-Data")
    return _validate_init_data(x_init_data)


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/data")
async def get_data(user: dict = Depends(get_user)):
    """Повертає всі збережені дані користувача."""
    uid = str(user["id"])
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() or {}


class SyncPayload(BaseModel):
    key: str
    data: Any


@app.post("/sync")
async def sync_data(payload: SyncPayload, user: dict = Depends(get_user)):
    """Зберігає одне key-value у Firestore."""
    uid = str(user["id"])
    # Видаляємо старі записи sets_ і meals_ старші 30 днів при кожному записі
    db.collection("users").document(uid).set(
        {payload.key: payload.data},
        merge=True,
    )
    log.info("Synced key=%s for user=%s", payload.key, uid)
    return {"ok": True}


@app.delete("/data")
async def delete_all(user: dict = Depends(get_user)):
    """Видаляє всі дані користувача (відповідає кнопці 'Видалити всі дані')."""
    uid = str(user["id"])
    db.collection("users").document(uid).delete()
    return {"ok": True}
