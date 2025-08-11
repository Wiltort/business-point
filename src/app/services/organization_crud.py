import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from .phone_crud import PhoneService
from .activity_crud import ActivityService
from .. import models, schemas
import math


class OrganizationService:
    """
    Service for asynchronous CRUD operations and queries on Organization entities.
    Provides methods for creating, retrieving, updating, deleting, and searching organizations,
    as well as filtering by building or activity.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the OrganizationService.

        Args:
            db (AsyncSession): The SQLAlchemy async session.
        """
        self.db = db
        self.phone_service = PhoneService(db)
        self.activity_service = ActivityService(db)

    async def create(self, organization: schemas.OrganizationCreate) -> models.Organization:
        """
        Create a new organization with associated phones and activities.

        Args:
            organization (schemas.OrganizationCreate): Data for the new organization.

        Returns:
            models.Organization: The created Organization model.
        """
        phones = await self.phone_service.get_phones_by_numbers(organization.phone_numbers)
        existing_numbers = {p.number for p in phones}
        new_phones = [
            models.Phone(number=num)
            for num in organization.phone_numbers
            if num not in existing_numbers
        ]
        activities = await asyncio.gather(
            *[self.activity_service.get(act_id) for act_id in organization.activity_ids]
        )
        activities = [a for a in activities if a is not None]
        db_organization = models.Organization(
            name=organization.name,
            building_id=organization.building_id,
            phones=phones + new_phones,
            activities=activities
        )
        self.db.add(db_organization)
        await self.db.commit()
        await self.db.refresh(db_organization)
        return db_organization

    async def get(self, organization_id: int) -> models.Organization | None:
        """
        Retrieve an organization by its ID.

        Args:
            organization_id (int): The ID of the organization.

        Returns:
            models.Organization | None: The Organization model if found, else None.
        """
        result = await self.db.execute(
            select(models.Organization).where(models.Organization.id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_list(self, skip: int = 0, limit: int = 100) -> list[models.Organization]:
        """
        Retrieve a paginated list of organizations.

        Args:
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 100.

        Returns:
            list[models.Organization]: List of Organization models.
        """
        result = await self.db.execute(
            select(models.Organization)
            .options(
                selectinload(models.Organization.phones),
                selectinload(models.Organization.activities),
                selectinload(models.Organization.building),
            )
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_building(self, building_id: int) -> list[models.Organization]:
        """
        Retrieve organizations by building ID.

        Args:
            building_id (int): The ID of the building.

        Returns:
            list[models.Organization]: List of organizations in the specified building.
        """
        result = await self.db.execute(
            select(models.Organization).where(models.Organization.building_id == building_id)
        )
        return result.scalars().all()

    async def get_by_activity(self, activity_id: int) -> list[models.Organization]:
        """
        Retrieve organizations associated with a given activity and its descendants.

        Args:
            activity_id (int): The ID of the activity.

        Returns:
            list[models.Organization]: List of organizations linked to the activity or its children.
        """
        activity = await self.activity_service.get(activity_id)
        if not activity:
            return []
        all_activity_ids = [activity_id] + await self.activity_service.get_all_children_ids(activity_id)
        if not all_activity_ids:
            return []
        result = await self.db.execute(
            select(models.Organization)
            .join(models.Organization.activities)
            .where(models.Activity.id.in_(all_activity_ids))
            .distinct()
        )
        return result.scalars().all()

    async def update(
        self,
        organization_id: int,
        organization: schemas.OrganizationUpdate
    ) -> models.Organization | None:
        """
        Update an existing organization by its ID.

        Args:
            organization_id (int): The ID of the organization to update.
            organization (schemas.OrganizationUpdate): The update data.

        Returns:
            models.Organization | None: The updated Organization model, or None if not found.
        """
        db_org = await self.get(organization_id)
        if not db_org:
            return None

        if organization.name is not None:
            db_org.name = organization.name
        if organization.building_id is not None:
            db_org.building_id = organization.building_id
        if organization.phone_numbers is not None:
            phones = await self.phone_service.get_phones_by_numbers(organization.phone_numbers)
            existing_numbers = {p.number for p in phones}
            new_phones = [
                models.Phone(number=num)
                for num in organization.phone_numbers
                if num not in existing_numbers
            ]
            db_org.phones = phones + new_phones
        if organization.activity_ids is not None:
            activities = await asyncio.gather(
                *[self.activity_service.get(act_id) for act_id in organization.activity_ids]
            )
            db_org.activities = [a for a in activities if a is not None]

        await self.db.commit()
        await self.db.refresh(db_org)
        return db_org

    async def delete(self, organization_id: int) -> bool:
        """
        Delete an organization by its ID.

        Args:
            organization_id (int): The ID of the organization to delete.

        Returns:
            bool: True if deleted, False if not found.
        """
        db_org = await self.get(organization_id)
        if not db_org:
            return False

        await self.db.delete(db_org)
        await self.db.commit()
        return True

    async def search(self, name: str) -> list[models.Organization]:
        """
        Search for organizations by name (case-insensitive, partial match).

        Args:
            name (str): The name or part of the name to search for.

        Returns:
            list[models.Organization]: List of organizations matching the search.
        """
        result = await self.db.execute(
            select(models.Organization).where(
                models.Organization.name.ilike(f"%{name}%")
            )
        )
        return result.scalars().all()

    async def get_by_radius(
            self,
            area: schemas.GeoSearchRadius
    ) -> list[models.Organization]:
        """
        Retrieve organizations located in buildings within a given radius from a point.
        Args:
            latitude (float): Latitude of the center point.
            longitude (float): Longitude of the center point.
            radius (float): Search radius.
            unit (str, optional): 'km' for kilometers or 'mi' for miles. Defaults to 'km'.
        Returns:
            list[models.Organization]: List of organizations in buildings within the radius.
        """

        earth_radius = 6371_000
        radius_in_m = area.unit.to_meters(area.radius)

        def haversine(lat1, lon1, lat2, lon2):
            # Convert decimal degrees to radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))
            return earth_radius * c

        result = await self.db.execute(select(models.Building))
        buildings = result.scalars().all()

        nearby_building_ids = [
            b.id for b in buildings
            if haversine(area.latitude, area.longitude, b.latitude, b.longitude) <= radius_in_m
        ]
        if not nearby_building_ids:
            return []
        # Get organizations in these buildings
        result = await self.db.execute(
            select(models.Organization).where(models.Organization.building_id.in_(nearby_building_ids))
        )
        return result.scalars().all()
