from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import re

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---- Replace this with YOUR real auth dependency ----
def get_current_user():
    """
    Replace with your actual auth dependency.
    Must return a user object/dict that represents the currently logged in user.
    """
    raise HTTPException(status_code=501, detail="get_current_user() not wired yet")


class UpdatePhoneIn(BaseModel):
    phone: str


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D+", "", phone)
    # Basic US validation: 10 digits or 11 digits starting with 1
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")
    return digits


@router.post("/update-phone")
async def update_phone(payload: UpdatePhoneIn, user=Depends(get_current_user)):
    phone = normalize_phone(payload.phone)

    # ✅ TODO: Save to your DB here.
    # Example patterns:
    #
    # user.phone = phone
    # db.add(user); db.commit(); db.refresh(user)
    #
    # OR if you store profile fields in a separate table:
    # profile.phone = phone; commit...

    # For now, return success so the frontend can proceed.
    return {"ok": True, "phone": phone}
