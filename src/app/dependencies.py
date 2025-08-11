import os
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_db
from .services.phone_crud import PhoneService
from .services.activity_crud import ActivityService
from .services.organization_crud import OrganizationService
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("API_KEY", "supersecretkey")


def api_key_auth(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )


def get_phone_service(db: AsyncSession = Depends(get_db)) -> PhoneService:
    return PhoneService(db)


def get_activity_service(db: AsyncSession = Depends(get_db)) -> ActivityService:
    return ActivityService(db)


def get_organization_service(db: AsyncSession = Depends(get_db)) -> OrganizationService:
    return OrganizationService(db)
