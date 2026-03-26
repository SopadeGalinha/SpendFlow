from fastapi import APIRouter

from .projection import router as projection_router
from .rule import router as rule_router

router = APIRouter()
router.include_router(projection_router)
router.include_router(rule_router)

__all__ = ["router"]
