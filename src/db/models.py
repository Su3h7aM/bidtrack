from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum as PyEnum
from typing import List, Optional
from sqlmodel import (
    Column,
    Enum,
    Field,
    Numeric,
    Relationship,
    SQLModel,
    DateTime,
)


class Quote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    item_id: Optional[int] = Field(foreign_key="item.id", nullable=False)
    supplier_id: Optional[int] = Field(foreign_key="supplier.id", nullable=False)

    price: Decimal = Field(
        sa_column=Column(Numeric(precision=20, scale=5, asdecimal=True))
    )
    margin: float
    notes: Optional[str] = Field(default=None)


class Bid(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    item_id: Optional[int] = Field(foreign_key="item.id", nullable=False)
    competitor_id: Optional[int] = Field(foreign_key="competitor.id", nullable=False)
    bidding_id: Optional[int] = Field(foreign_key="bidding.id", nullable=False)

    notes: Optional[str] = Field(default=None)

    price: Decimal = Field(
        sa_column=Column(Numeric(precision=20, scale=5, asdecimal=True))
    )


class BiddingMode(str, PyEnum):
    PP = "Pregão Presencial"
    PE = "Pregão Eletrônico"


class Bidding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    city: str
    session_date: Optional[date] = Field(default=None)
    session_time: Optional[time] = Field(default=None)
    mode: BiddingMode = Field(sa_column=Column(Enum(BiddingMode)))
    process_number: str

    items: Optional[List["Item"]] = Relationship(back_populates="bidding")


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    name: str = Field(unique=True)
    desc: Optional[str] = Field(default=None)
    unit: Optional[str] = Field(default=None)
    quantity: float

    bidding_id: Optional[int] = Field(foreign_key="bidding.id", nullable=False)

    bidding: Optional[Bidding] = Relationship(back_populates="items")
    suppliers: Optional[List["Supplier"]] = Relationship(
        back_populates="items", link_model=Quote
    )
    competitors: Optional[List["Competitor"]] = Relationship(
        back_populates="items", link_model=Bid
    )


class Supplier(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    name: str = Field(unique=True)
    website: Optional[str] = Field(default=None, unique=True)
    email: Optional[str] = Field(default=None, unique=True)
    phone: Optional[str] = Field(default=None, unique=True)
    desc: Optional[str] = Field(default=None)

    items: Optional[List["Item"]] = Relationship(
        back_populates="suppliers", link_model=Quote
    )


class Competitor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    name: str = Field(unique=True)
    website: Optional[str] = Field(default=None, unique=True)
    email: Optional[str] = Field(default=None, unique=True)
    phone: Optional[str] = Field(default=None, unique=True)
    desc: Optional[str] = Field(default=None)

    items: Optional[List["Item"]] = Relationship(
        back_populates="competitors", link_model=Bid
    )
