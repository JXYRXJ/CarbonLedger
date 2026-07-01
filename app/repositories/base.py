from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy import func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic Base Repository implementing standard CRUD operations with SQLAlchemy 2.0.
    Handles soft-delete exclusions automatically if the model has a `deleted_at` attribute.
    """
    def __init__(self, model: Type[T], db: Session) -> None:
        self.model = model
        self.db = db

    def create(self, obj_in: Union[Dict[str, Any], Any]) -> T:
        """
        Creates a new record from dictionary or Pydantic model.
        """
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = self.model(**obj_in.model_dump())
            
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: T, obj_in: Union[Dict[str, Any], Any]) -> T:
        """
        Updates an existing record.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: T) -> None:
        """
        Hard deletes a record from the database.
        """
        self.db.delete(db_obj)
        self.db.commit()

    def soft_delete(self, db_obj: T) -> T:
        """
        Soft deletes a record by setting `deleted_at` timestamp if supported.
        """
        if hasattr(db_obj, "deleted_at"):
            setattr(db_obj, "deleted_at", datetime.now(timezone.utc))
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def find_by_id(self, id: Any) -> Optional[T]:
        """
        Finds a record by primary key UUID. Excludes soft-deleted items.
        """
        stmt = select(self.model).where(self.model.id == id)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at == None)
        return self.db.execute(stmt).scalar_one_or_none()

    def find_one(self, **filters) -> Optional[T]:
        """
        Finds a single record based on keyword filter arguments.
        """
        stmt = select(self.model).filter_by(**filters)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at == None)
        return self.db.execute(stmt).scalars().first()

    def find_many(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_field: Optional[str] = None,
        sort_order: str = "asc",
        **filters
    ) -> List[T]:
        """
        Finds multiple records based on filters, pagination, and sorting.
        """
        stmt = select(self.model).filter_by(**filters)
        
        # Apply soft-delete filter
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at == None)
            
        # Apply sorting
        if sort_field and hasattr(self.model, sort_field):
            col = getattr(self.model, sort_field)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(col.desc())
            else:
                stmt = stmt.order_by(col.asc())
        elif hasattr(self.model, "created_at"):
            stmt = stmt.order_by(getattr(self.model, "created_at").desc())

        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def exists(self, id: Any) -> bool:
        """
        Checks if a record exists.
        """
        return self.find_by_id(id) is not None

    def count(self, **filters) -> int:
        """
        Counts total records matching filters.
        """
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at == None)
        return self.db.execute(stmt).scalar() or 0

    def paginate(
        self,
        page: int = 1,
        limit: int = 10,
        sort_field: Optional[str] = None,
        sort_order: str = "asc",
        **filters
    ) -> tuple[List[T], int]:
        """
        Returns paginated items and total count.
        """
        skip = (page - 1) * limit
        total = self.count(**filters)
        items = self.find_many(
            skip=skip,
            limit=limit,
            sort_field=sort_field,
            sort_order=sort_order,
            **filters
        )
        return items, total
