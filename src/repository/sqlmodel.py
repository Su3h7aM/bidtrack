from typing import override, Any
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine, Session, select

from .interface import Repository # Updated import for the interface


class SQLModelRepository[T: SQLModel](Repository[T]):
    def __init__(
        self, model: type[T], db_url: str = "sqlite:///data/bidtrack.db"
    ) -> None:
        self.model: type[T] = model
        self.engine: Engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine) # Ensure tables are created

    @override
    def add(self, item: T) -> T:
        with Session(self.engine) as session:
            if hasattr(item, "id"): # Manage ID for new records
                item.id = None
            # created_at and updated_at are often handled by model defaults or DB
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
            return list(all_items) # Ensure a list is returned

    @override
    def update(self, item_id: int, item_data: dict[str, Any]) -> T | None:
        with Session(self.engine) as session:
            db_item = session.get(self.model, item_id)
            if db_item:
                item_changed = False
                for key, value in item_data.items():
                    # Ensure not to update primary key or protected fields directly
                    if key not in ["id", "created_at", "updated_at"] and hasattr(db_item, key):
                        if getattr(db_item, key) != value:
                            setattr(db_item, key, value)
                            item_changed = True
                if item_changed:
                    # Handle 'updated_at' if it's a model concern and not purely DB
                    if hasattr(db_item, "updated_at"):
                        from datetime import datetime # Conditional import
                        setattr(db_item, "updated_at", datetime.now())
                    session.add(db_item)
                    session.commit()
                    session.refresh(db_item)
            return db_item

    @override
    def delete(self, id: int) -> bool:
        with Session(self.engine) as session:
            item_to_delete = session.get(self.model, id)
            if item_to_delete:
                session.delete(item_to_delete)
                session.commit()
                return True
            return False
