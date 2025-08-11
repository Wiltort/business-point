from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from .. import schemas, models
from sqlalchemy import select


class BuildingService:
    """
    Service for asynchronous CRUD operations and queries on Building entities.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the BuildingService.

        Args:
            db (AsyncSession): The SQLAlchemy async session.
        """
        self.db = db

    async def get(self, id: int) -> models.Building | None:
        """
        Retrieve a Building by its ID.

        Args:
            id (int): The ID of building.

        Returns:
            models.Building | None: The Building model if found, else None.
        """
        result = await self.db.execute(
            select(models.Building).where(models.Building.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, building: schemas.BuildingCreate) -> models.Building:
        """
        Create a new building.

        Args:
            building (schemas.BuildingCreate): Data for the building to create.

        Returns:
            models.Building: The created building model.
        """
        db_building = models.Building(
            address=building.address,
            latitude=building.latitude,
            longitude=building.longitude
        )
        self.db.add(db_building)
        await self.db.commit()
        await self.db.refresh(db_building)
        return db_building
