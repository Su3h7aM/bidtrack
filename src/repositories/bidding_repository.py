# src/repositories/bidding_repository.py
from src.db.models import Bidding
from src.db.repository import BaseRepository

class BiddingRepository(BaseRepository[Bidding, Bidding, Bidding]):
    def __init__(self):
        super().__init__(model=Bidding)

# You can add Bidding-specific methods here later if needed
