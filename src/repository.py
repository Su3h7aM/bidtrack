from abc import ABC, abstractmethod
from typing import override
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine, Session, select
from db.models import Quote, Supplier


class Repository[T](ABC):
    @abstractmethod
    def add(self, item: T) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, id: int) -> T | None:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[T] | None:
        raise NotImplementedError


class SQLModelRepository[T](Repository[T]):
    def __init__(
        self, model: type[T], db_url: str = "sqlite:///data/bidtrack.db"
    ) -> None:
        self.model: type[T] = model
        self.engine: Engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)
        self.session: Session = Session(self.engine)

    @override
    def add(self, item: T) -> None:
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)

    @override
    def get(self, id: int) -> T | None:
        return self.session.get(self.model, id)

    @override
    def get_all(self) -> list[T] | None:
        statement = select(self.model)
        all = self.session.exec(statement).all()
        return list(all)


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
