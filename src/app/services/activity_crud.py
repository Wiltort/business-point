from sqlalchemy.ext.asyncio import AsyncSession
from .. import schemas, models
from sqlalchemy import select
from sqlalchemy.orm import aliased


class ActivityService:
    """
    Service for asynchronous operations with the Activity entity.

    Provides methods for creating, retrieving, updating, deleting,
    and building an activity tree.
    """
    def __init__(self, db: AsyncSession):
        """
        Initialize the ActivityService.

        Args:
            db (AsyncSession): SQLAlchemy asynchronous session.
        """
        self.db = db

    async def create(self, activity: schemas.ActivityCreate) -> models.Activity:
        """
        Create a new activity.

        Args:
            activity (schemas.ActivityCreate): Data for the new activity.

        Returns:
            models.Activity: The created Activity model.
        """
        db_activity = models.Activity(
            name=activity.name,
            parent_id=activity.parent_id
        )
        self.db.add(db_activity)
        await self.db.commit()
        await self.db.refresh(db_activity)
        return db_activity

    async def get(self, activity_id: int) -> models.Activity | None:
        """
        Retrieve an activity by its ID.

        Args:
            activity_id (int): The activity ID.

        Returns:
            models.Activity | None: The Activity model if found, otherwise None.
        """
        result = await self.db.execute(
            select(models.Activity).where(models.Activity.id == activity_id)
        )
        return result.scalar_one_or_none()

    async def get_list(self, skip: int = 0, limit: int = 100) -> list[models.Activity]:
        """
        Retrieve a paginated list of activities.

        Args:
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 100.

        Returns:
            list[models.Activity]: List of Activity models.
        """
        result = await self.db.execute(
            select(models.Activity).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_child_activities(self, parent_id: int) -> list[models.Activity]:
        """
        Retrieve direct child activities for a given parent activity ID.

        Args:
            parent_id (int): The parent activity ID.

        Returns:
            list[models.Activity]: List of child Activity models.
        """
        result = await self.db.execute(
            select(models.Activity).where(models.Activity.parent_id == parent_id)
        )
        return result.scalars().all()

    async def update(self, activity_id: int, activity_update: schemas.ActivityUpdate) -> models.Activity | None:
        """
        Update an activity by its ID.

        Args:
            activity_id (int): The activity ID.
            activity_update (schemas.ActivityUpdate): Data for updating the activity.

        Returns:
            models.Activity | None: The updated Activity model if found, otherwise None.
        """
        db_activity = await self.get(activity_id)
        if not db_activity:
            return None
        if activity_update.name is not None:
            db_activity.name = activity_update.name
        if activity_update.parent_id is not None:
            db_activity.parent_id = activity_update.parent_id
        await self.db.commit()
        await self.db.refresh(db_activity)
        return db_activity

    async def delete(self, activity_id: int) -> bool:
        """
        Delete an activity by its ID.

        Args:
            activity_id (int): The activity ID.

        Returns:
            bool: True if deleted, False if not found.
        """
        db_activity = await self.get(activity_id)
        if not db_activity:
            return False
        await self.db.delete(db_activity)
        await self.db.commit()
        return True

    async def get_all_children_ids(self, parent_id: int) -> list[int]:
        """
        Get a list of IDs for all descendant activities (all levels) for a given parent activity.

        Args:
            parent_id (int): The parent activity ID.

        Returns:
            list[int]: List of descendant activity IDs.
        """
        actv = aliased(models.Activity, name="actv")
        tree = (
            select(actv.id)
            .where(actv.parent_id == parent_id)
            .cte(recursive=True, name="tree")
        )
        prnt = aliased(models.Activity, name="prnt")
        recursive_part = (
            select(actv.id)
            .join(prnt, actv.parent_id == prnt.id)
            .join(tree, prnt.id == tree.c.id)
        )
        cte_query = tree.union_all(recursive_part)
        res = await self.db.execute(cte_query.c.id)
        return res.unique().scalars().all()

    async def get_activity_tree(self, parent_id: int | None = None) -> list[schemas.ActivityTree]:
        """
        Build and return an activity tree starting from the given parent_id (or root nodes if parent_id is None),
        formatted as a list of schemas.ActivityTree.

        Args:
            parent_id (int | None, optional): The parent activity ID or None for root activities.

        Returns:
            list[schemas.ActivityTree]: List of root nodes of the activity tree.
        """
        actv = aliased(models.Activity, name="actv")
        tree = (
            select(actv)
            .where(actv.parent_id == parent_id)
            .cte(recursive=True, name="tree")
        )
        prnt = aliased(models.Activity, name="prnt")
        recursive_part = (
            select(actv)
            .join(prnt, actv.parent_id == prnt.id)
            .join(tree, prnt.id == tree.c.id)
        )
        cte_query = tree.union_all(recursive_part)
        res = await self.db.execute(cte_query)
        activities = res.unique().scalars().all()
        id_to_tree: dict[int, schemas.ActivityTree] = {}
        children_map: dict[int | None, list[schemas.ActivityTree]] = {}

        for activity in activities:
            node = schemas.ActivityTree(
                id=activity.id,
                name=activity.name,
                parent_id=activity.parent_id,
                children=[]
            )
            id_to_tree[activity.id] = node
            children_map.setdefault(activity.parent_id, []).append(node)

        def attach_children(node: schemas.ActivityTree):
            node.children = children_map.get(node.id, [])
            for child in node.children:
                attach_children(child)

        roots = children_map.get(parent_id, [])
        for root in roots:
            attach_children(root)

        return roots
