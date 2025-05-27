# src/repositories/item_repository.py
from src.db.models import Item
from src.db.repository import BaseRepository

class ItemRepository(BaseRepository[Item, Item, Item]):
    def __init__(self):
        super().__init__(model=Item)

# You can add Item-specific methods here later if needed
