from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    bidding_id: Optional[int] = Field(default=None, foreign_key="bidding.id")
    bidding: Optional["Bidding"] = Relationship(back_populates="items")

class Bidding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    items: List[Item] = Relationship(back_populates="bidding")
