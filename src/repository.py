from abc import ABC, abstractmethod
from typing import override
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine, Session, select


class Repository[T](ABC):
    @abstractmethod
    def add(self, item: T) -> T:  # Changed return type to T
        raise NotImplementedError

    @abstractmethod
    def get(self, id: int) -> T | None:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[T]:
        raise NotImplementedError

    @abstractmethod
    def update(self, item_id: int, item_data: T) -> T | None:
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
        # self.session: Session = Session(self.engine) # Session should be created per request or context
        self._sessionmaker = Session(self.engine)  # Store the session factory

    # It's generally better to manage session scope, e.g., per request in a web app,
    # or per operation for command-line tools. For this Streamlit app,
    # a new session per method call or a short-lived session might be appropriate.
    # For simplicity here, let's create a new session if one isn't active,
    # but be mindful this isn't ideal for all scenarios.
    @property
    def session(self) -> Session:
        # This is a simplified session management. In a real app, use context managers.
        # For Streamlit, this might be okay if operations are relatively atomic.
        # If _sessionmaker is already a session instance due to previous __init__
        if isinstance(self._sessionmaker, Session) and self._sessionmaker.is_active:
            return self._sessionmaker
        # Otherwise, create a new session from the engine if _sessionmaker was the factory
        # For now, let's assume self.engine is what we want to use for new sessions.
        return Session(self.engine)

    @override
    def add(self, item: T) -> T:  # Changed return type to T
        # Use a context manager for session once session management is refined
        current_session = self.session

        # Ensure ID and timestamps are managed by the database for new records
        if hasattr(item, "id"):
            item.id = None
        if hasattr(item, "created_at"):
            item.created_at = None
        if hasattr(item, "updated_at"):
            item.updated_at = None

        current_session.add(item)
        current_session.commit()
        current_session.refresh(item)
        return item

    @override
    def get(self, id: int) -> T | None:
        return self.session.get(self.model, id)

    @override
    def get_all(self) -> list[T]:
        statement = select(self.model)
        all_items = self.session.exec(statement).all()
        return list(all_items)

    @override
    def update(self, item_id: int, item_data: T) -> T | None:
        current_session = self.session
        db_item = current_session.get(self.model, item_id)
        if db_item:
            # Exclude 'id', 'created_at', and 'updated_at' from data_to_update
            filtered_data = {
                k: v
                for k, v in data_to_update.items()
                if k not in ["id", "created_at", "updated_at"]
            }
            for key, value in filtered_data.items():
                if hasattr(db_item, key):  # Ensure the attribute exists
                    setattr(db_item, key, value)
            current_session.add(db_item)  # Re-adding is often good practice
            current_session.commit()
            current_session.refresh(db_item)
        return db_item

    @override
    def delete(self, id: int) -> bool:
        current_session = self.session
        item = current_session.get(self.model, id)
        if item:
            current_session.delete(item)
            current_session.commit()
            return True
        return False


# Exemplo de uso:
#
# repo = SQLModelRepository(Supplier)
# pichau = Supplier(name="Nova Pichau", desc="Nova descriçao da loja")
# repo.add(pichau)
# t = repo.get(pichau.id)
# a = repo.get_all()
#
# print(t)
# print("--------------------------")
# print(a)
