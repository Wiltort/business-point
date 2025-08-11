from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from . import schemas
from .dependencies import (
    get_phone_service,
    get_activity_service,
    get_organization_service,
    api_key_auth,
)
from .services.phone_crud import PhoneService
from .services.activity_crud import ActivityService
from .services.organization_crud import OrganizationService

router = APIRouter(dependencies=[Depends(api_key_auth)])


# --- Organization Routes ---

@router.post("/organizations/", response_model=schemas.Organization)
async def create_organization(
    org: schemas.OrganizationCreate,
    service: OrganizationService = Depends(get_organization_service),
):
    return await service.create(org)

@router.get("/organizations/{org_id}", response_model=schemas.Organization)
async def get_organization(
    org_id: int,
    service: OrganizationService = Depends(get_organization_service),
):
    org = await service.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.get("/organizations/", response_model=List[schemas.Organization])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    service: OrganizationService = Depends(get_organization_service),
):
    return await service.get_list(skip=skip, limit=limit)

@router.put("/organizations/{org_id}", response_model=schemas.Organization)
async def update_organization(
    org_id: int,
    org_update: schemas.OrganizationUpdate,
    service: OrganizationService = Depends(get_organization_service),
):
    org = await service.update(org_id, org_update)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.delete("/organizations/{org_id}", response_model=bool)
async def delete_organization(
    org_id: int,
    service: OrganizationService = Depends(get_organization_service),
):
    result = await service.delete(org_id)
    if not result:
        raise HTTPException(status_code=404, detail="Organization not found")
    return result

@router.post("/organizations/by_radius/", response_model=List[schemas.Organization])
async def organizations_by_radius(
    area: schemas.GeoSearchRadius,
    service: OrganizationService = Depends(get_organization_service),
):
    """
    Получить список организаций, находящихся в зданиях в заданном радиусе от точки.
    """
    return await service.get_by_radius(area)

# --- Phone Routes ---

@router.get("/phones/{phone_id}", response_model=schemas.Phone)
async def get_phone(
    phone_id: int,
    service: PhoneService = Depends(get_phone_service),
):
    phone = await service.get(phone_id)
    if not phone:
        raise HTTPException(status_code=404, detail="Phone not found")
    return phone

@router.delete("/phones/{phone_id}", response_model=bool)
async def delete_phone(
    phone_id: int,
    service: PhoneService = Depends(get_phone_service),
):
    result = await service.delete(phone_id)
    if not result:
        raise HTTPException(status_code=404, detail="Phone not found")
    return result

# --- Activity Routes ---

@router.post("/activities/", response_model=schemas.Activity)
async def create_activity(
    activity: schemas.ActivityCreate,
    service: ActivityService = Depends(get_activity_service),
):
    if activity.parent_id:
        if not service.is_level_less_than_3(activity.parent_id):
            return HTTPException(status_code=401, detail="Level is bigger than 3")
    return await service.create(activity)

@router.get("/activities/{activity_id}", response_model=schemas.ActivityRead)
async def get_activity(
    activity_id: int,
    service: ActivityService = Depends(get_activity_service),
):
    activity = await service.get(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

@router.get("/activities/", response_model=List[schemas.ActivityRead])
async def list_activities(
    skip: int = 0,
    limit: int = 100,
    service: ActivityService = Depends(get_activity_service),
):
    return await service.get_list(skip=skip, limit=limit)

@router.put("/activities/{activity_id}", response_model=schemas.Activity)
async def update_activity(
    activity_id: int,
    activity_update: schemas.ActivityUpdate,
    service: ActivityService = Depends(get_activity_service),
):
    activity = await service.update(activity_id, activity_update)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

@router.delete("/activities/{activity_id}", response_model=bool)
async def delete_activity(
    activity_id: int,
    service: ActivityService = Depends(get_activity_service),
):
    result = await service.delete(activity_id)
    if not result:
        raise HTTPException(status_code=404, detail="Activity not found")
    return result

@router.get("/activities/tree/", response_model=List[schemas.ActivityTree])
async def get_activity_tree(
    parent_id: Optional[int] = Query(None),
    service: ActivityService = Depends(get_activity_service),
):
    return await service.get_activity_tree(parent_id=parent_id)
