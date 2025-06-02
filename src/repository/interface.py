from abc import ABC, abstractmethod
from typing import Any # For dict[str, Any] in update method

# Python 3.9+ allows built-in types like list for generics, so no 'from typing import list'

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
