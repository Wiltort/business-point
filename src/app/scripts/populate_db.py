import asyncio
from dotenv import load_dotenv
import os
from app.db import get_db
from app.services.organization_crud import OrganizationService
from app.services.activity_crud import ActivityService
from app.services.phone_crud import PhoneService
from app.services.building_crud import BuildingService
from app import schemas
from sqlalchemy import text


load_dotenv()


async def clear_database(db):
    await db.execute(text("DELETE FROM organization_activity"))
    await db.execute(text("DELETE FROM phones"))
    await db.execute(text("DELETE FROM organizations"))
    await db.execute(text("DELETE FROM activities"))
    await db.execute(text("DELETE FROM buildings"))
    await db.commit()


async def populate():
    async for db in get_db():
        await clear_database(db)

        org_service = OrganizationService(db)
        act_service = ActivityService(db)
        phone_service = PhoneService(db)
        building_service = BuildingService(db)

        # Создание зданий
        building1_data = schemas.BuildingCreate(
            address="ул. Ленина, 1",
            latitude=55.7558,
            longitude=37.6176
        )
        building2_data = schemas.BuildingCreate(
            address="пр. Мира, 10",
            latitude=55.7890,
            longitude=37.6789
        )
        building1 = await building_service.create(building=building1_data)
        building2 = await building_service.create(building=building2_data)

        # Создание активностей
        activity1_data = schemas.ActivityCreate(name="Образование")
        activity1 = await act_service.create(activity1_data)
        activity2_data = schemas.ActivityCreate(name="Спорт", parent_id=activity1.id)
        activity3_data = schemas.ActivityCreate(name="Культура")
        activity2 = await act_service.create(activity2_data)
        activity3 = await act_service.create(activity3_data)

        # Создание организаций
        org1_data = schemas.OrganizationCreate(
            name="Школа №1",
            building_id=building1.id,
            activity_ids=[activity1.id]
        )
        org2_data = schemas.OrganizationCreate(
            name="ДЮСШ",
            building_id=building2.id,
            activity_ids=[activity2.id, activity3.id]
        )
        org1 = await org_service.create(org1_data)
        org2 = await org_service.create(org2_data)

        # Добавление телефонов
        phone1_data = schemas.PhoneCreate(
            number="+7-495-111-2233",
            organization_id=org1.id
        )
        phone2_data = schemas.PhoneCreate(
            number="+7-495-222-3344",
            organization_id=org2.id
        )
        phone1 = await phone_service.create_or_update(phone1_data)
        phone2 = await phone_service.create_or_update(phone2_data)

        print("Тестовые данные успешно добавлены!")


if __name__ == "__main__":
    asyncio.run(populate())