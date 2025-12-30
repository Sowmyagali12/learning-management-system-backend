from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import UserOut

router = APIRouter(prefix="/student", tags=["student"])



@router.get("/StudentDetails", response_model=UserOut)
def get_my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return current_user