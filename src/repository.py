from abc import ABC, abstractmethod
from typing import override, Any
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine, Session, select


class Repository[T](ABC):
    @abstractmethod
    def add(self, item: T) -> T:
        raise NotImplementedError

    @abstractmethod
    def get(self, id: int) -> T | None:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[T]:
        raise NotImplementedError

    @abstractmethod
    def update(self, item_id: int, item_data: dict[str, Any]) -> T | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, id: int) -> bool:
        raise NotImplementedError


class SQLModelRepository[T: SQLModel](Repository[T]):
    def __init__(
        self, model: type[T], db_url: str = "sqlite:///data/bidtrack.db"
    ) -> None:
        self.model: type[T] = model
        self.engine: Engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)

    @override
    def add(self, item: T) -> T:
        with Session(self.engine) as session:
            # Ensure ID and timestamps are managed by the database for new records
            if hasattr(item, "id"):
                item.id = None
            # created_at and updated_at are typically handled by the database or model defaults
            # So, no need to set them to None here if they have default_factory in model
            session.add(item)
            session.commit()
            session.refresh(item)
            return item

    @override
    def get(self, id: int) -> T | None:
        with Session(self.engine) as session:
            return session.get(self.model, id)

    @override
    def get_all(self) -> list[T]:
        with Session(self.engine) as session:
            statement = select(self.model)
            all_items = session.exec(statement).all()
            return list(all_items)

    @override
    def update(self, item_id: int, item_data: dict[str, Any]) -> T | None:
        with Session(self.engine) as session:
            db_item = session.get(self.model, item_id)
            if db_item:
                # Exclude 'id', 'created_at', and 'updated_at' from item_data
                for key, value in item_data.items():
                    if key not in ["id", "created_at", "updated_at"] and hasattr(db_item, key):
                        setattr(db_item, key, value)
                session.add(db_item)
                session.commit()
                session.refresh(db_item)
            return db_item

    @override
    def delete(self, id: int) -> bool:
        with Session(self.engine) as session:
            item = session.get(self.model, id)
            if item:
                session.delete(item)
                session.commit()
                return True
            return False
