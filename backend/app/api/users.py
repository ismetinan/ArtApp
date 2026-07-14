from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.tables import User

router = APIRouter(prefix="/users", tags=["users"])


class GuestRequest(BaseModel):
    display_name: str = "Misafir Çizer"


class UserOut(BaseModel):
    id: int
    display_name: str
    is_guest: bool
    level: int
    xp: int

    model_config = {"from_attributes": True}


@router.post("/guest", response_model=UserOut)
def create_guest(body: GuestRequest, db: Session = Depends(get_db)):
    user = User(display_name=body.display_name, is_guest=True)
    db.add(user)
    db.commit()
    return user
