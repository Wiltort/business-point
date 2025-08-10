from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from .. import schemas, models
from sqlalchemy import select


class PhoneRaceConditionError(Exception):
    """
    Exception raised when a race condition cannot be resolved during phone creation.
    """
    pass


class PhoneService:
    """
    Service for asynchronous CRUD operations and queries on Phone entities.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the PhoneService.

        Args:
            db (AsyncSession): The SQLAlchemy async session.
        """
        self.db = db

    async def get_by_number(self, number: str) -> models.Phone | None:
        """
        Retrieve a phone by its number.

        Args:
            number (str): The phone number.

        Returns:
            models.Phone | None: The Phone model if found, else None.
        """
        result = await self.db.execute(
            select(models.Phone).where(models.Phone.number == number)
        )
        return result.scalar_one_or_none()

    async def create_or_update(self, phone: schemas.PhoneCreate) -> models.Phone:
        """
        Create a new phone or update the organization_id of an existing phone with the same number.
        Handles race conditions by retrying on IntegrityError.

        Args:
            phone (schemas.PhoneCreate): Data for the phone to create or update.

        Returns:
            models.Phone: The created or updated Phone model.

        Raises:
            PhoneRaceConditionError: If the phone cannot be created or fetched after an IntegrityError.
        """
        db_phone = await self.get_by_number(phone.number)
        if db_phone:
            db_phone.organization_id = phone.organization_id
            await self.db.commit()
            await self.db.refresh(db_phone)
            return db_phone
        else:
            db_phone = models.Phone(
                number=phone.number,
                organization_id=phone.organization_id
            )
            self.db.add(db_phone)
            try:
                await self.db.commit()
                await self.db.refresh(db_phone)
                return db_phone
            except IntegrityError:
                await self.db.rollback()
                db_phone = await self.get_by_number(phone.number)
                if db_phone:
                    db_phone.organization_id = phone.organization_id
                    await self.db.commit()
                    await self.db.refresh(db_phone)
                    return db_phone
                else:
                    raise PhoneRaceConditionError(
                        f"Failed to create or fetch phone with "
                        f"number {phone.number} after IntegrityError."
                    )

    async def get(self, phone_id: int) -> models.Phone | None:
        """
        Retrieve a phone by its id.

        Args:
            phone_id (int): The phone's id.

        Returns:
            models.Phone | None: The Phone model if found, else None.
        """
        result = await self.db.execute(
            select(models.Phone).where(models.Phone.id == phone_id)
        )
        return result.scalar_one_or_none()

    async def get_phones_by_numbers(self, numbers: list[str]) -> list[models.Phone]:
        """
        Retrieve a list of phones by their numbers.

        Args:
            numbers (list[str]): List of phone numbers.

        Returns:
            list[models.Phone]: List of Phone models matching the numbers.
        """
        if not numbers:
            return []
        result = await self.db.execute(
            select(models.Phone).where(models.Phone.number.in_(numbers))
        )
        return result.scalars().all()

    async def delete(self, phone_id: int) -> bool:
        """
        Delete a phone by its id.

        Args:
            phone_id (int): The phone's id.

        Returns:
            bool: True if the phone was deleted, False if not found.
        """
        db_phone = await self.get(phone_id)
        if not db_phone:
            return False
        await self.db.delete(db_phone)
        await self.db.commit()
        return True
