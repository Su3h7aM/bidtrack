from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
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
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    item_id: int | None = Field(foreign_key="item.id", nullable=False)
    supplier_id: int | None = Field(foreign_key="supplier.id", nullable=False)

    price: Decimal = Field(
        sa_column=Column(Numeric(precision=20, scale=5, asdecimal=True))
    )
    margin: float
    notes: str | None = Field(default=None)


class Bid(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    item_id: int | None = Field(foreign_key="item.id", nullable=False)
    competitor_id: int | None = Field(foreign_key="competitor.id", nullable=False)
    bidding_id: int | None = Field(foreign_key="bidding.id", nullable=False)

    notes: str | None = Field(default=None)

    price: Decimal = Field(
        sa_column=Column(Numeric(precision=20, scale=5, asdecimal=True))
    )


class BiddingMode(str, PyEnum):
    PP = "Pregão Presencial"
    PE = "Pregão Eletrônico"


class Bidding(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    city: str
    date: datetime | None = Field(default=None)
    mode: BiddingMode = Field(sa_column=Column(Enum(BiddingMode)))
    process_number: str

    items: list["Item"] | None = Relationship(back_populates="bidding")


class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    name: str = Field(unique=True)
    desc: str | None = Field(default=None)
    unit: str | None = Field(default=None)
    quantity: float

    bidding_id: int | None = Field(foreign_key="bidding.id", nullable=False)

    bidding: Bidding | None = Relationship(back_populates="items")
    suppliers: list["Supplier"] | None = Relationship(
        back_populates="items", link_model=Quote
    )
    competitors: list["Competitor"] | None = Relationship(
        back_populates="items", link_model=Bid
    )


class Supplier(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    name: str = Field(unique=True)
    website: str | None = Field(default=None, unique=True)
    email: str | None = Field(default=None, unique=True)
    phone: str | None = Field(default=None, unique=True)
    desc: str | None = Field(default=None)

    items: list["Item"] | None = Relationship(
        back_populates="suppliers", link_model=Quote
    )


class Competitor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    update_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    name: str = Field(unique=True)
    website: str | None = Field(default=None, unique=True)
    email: str | None = Field(default=None, unique=True)
    phone: str | None = Field(default=None, unique=True)
    desc: str | None = Field(default=None)

    items: list["Item"] | None = Relationship(
        back_populates="competitors", link_model=Bid
    )
