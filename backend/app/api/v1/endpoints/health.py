from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
def app_health():
    return {"status": True}