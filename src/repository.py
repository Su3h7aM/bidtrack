from abc import ABC, abstractmethod
from typing import override, TypeVar, Generic, Type, Optional, Any, List
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine, Session, select

ModelT = TypeVar("ModelT", bound=SQLModel)

class Repository(ABC, Generic[ModelT]): # Made base Repository also use ModelT for consistency
    @abstractmethod
    def add(self, item: ModelT) -> ModelT:
        raise NotImplementedError

    @abstractmethod
    def get(self, id: int) -> Optional[ModelT]:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> Optional[List[ModelT]]: # Adjusted to Optional[List[ModelT]]
        raise NotImplementedError

    @abstractmethod
    def update(self, item_id: int, item_data: dict[str, Any]) -> Optional[ModelT]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, id: int) -> bool:
        raise NotImplementedError


class SQLModelRepository(Repository[ModelT], Generic[ModelT]):
    def __init__(
        self, model_class: Type[ModelT], db_url: str = "sqlite:///data/bidtrack.db" # Changed 'model' to 'model_class'
    ) -> None:
        self.model_class: Type[ModelT] = model_class # Changed 'model' to 'model_class'
        self.engine: Engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine) # This should be called once, ideally not in __init__ of every repo instance
        self._sessionmaker = Session(self.engine)

    @property
    def session(self) -> Session:
        if isinstance(self._sessionmaker, Session) and self._sessionmaker.is_active:
             return self._sessionmaker
        return Session(self.engine)


    @override
    def add(self, item: ModelT) -> ModelT:
        current_session = self.session
        current_session.add(item)
        current_session.commit()
        current_session.refresh(item)
        return item

    @override
    def get(self, id: int) -> Optional[ModelT]: # Changed T | None to Optional[ModelT]
        return self.session.get(self.model_class, id)

    @override
    def get_all(self) -> Optional[List[ModelT]]: # Changed list[T] | None to Optional[List[ModelT]]
        statement = select(self.model_class)
        all_items = self.session.exec(statement).all()
        return list(all_items) if all_items is not None else None # Ensure None is returned if query result is None

    @override
    def update(self, item_id: int, item_data: dict[str, Any]) -> Optional[ModelT]: # Changed T | None to Optional[ModelT]
        current_session = self.session
        db_item = current_session.get(self.model_class, item_id)
        if db_item:
            for key, value in item_data.items(): # Changed data_to_update to item_data
                if hasattr(db_item, key):
                    setattr(db_item, key, value)
            current_session.add(db_item)
            current_session.commit()
            current_session.refresh(db_item)
        return db_item

    @override
    def delete(self, id: int) -> bool:
        current_session = self.session
        item = current_session.get(self.model_class, id) # Fixed self.model to self.model_class
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
