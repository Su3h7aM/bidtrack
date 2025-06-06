from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional  # Added import
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
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    item_id: int | None = Field(
        foreign_key="item.id", nullable=False, ondelete="CASCADE"
    )
    supplier_id: int | None = Field(
        foreign_key="supplier.id", nullable=False, ondelete="CASCADE"
    )

    price: Decimal = Field(  # This is the Custo do Produto
        sa_column=Column(Numeric(precision=20, scale=5, asdecimal=True))
    )
    # New fields
    freight: Decimal | None = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(precision=20, scale=5, asdecimal=True), nullable=True),
    )
    additional_costs: Decimal | None = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(precision=20, scale=5, asdecimal=True), nullable=True),
    )
    taxes: Decimal | None = Field(  # Percentage value, e.g., 6 for 6%
        default=Decimal("0.00"),
        sa_column=Column(
            Numeric(precision=5, scale=2, asdecimal=True), nullable=True
        ),  # Max 999.99%
    )

    margin: float  # This might need re-evaluation or be calculated differently now
    notes: str | None = Field(default=None)
    link: Optional[str] = Field(default=None, nullable=True) # New field


class Bid(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    item_id: int | None = Field(
        foreign_key="item.id", nullable=False, ondelete="CASCADE"
    )
    bidder_id: int | None = Field(
        default=None, foreign_key="bidder.id", nullable=True, ondelete="SET NULL"
    )  # Now optional
    bidding_id: int | None = Field(
        foreign_key="bidding.id", nullable=False, ondelete="CASCADE"
    )

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
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    city: str
    date: datetime | None = Field(default=None)
    mode: BiddingMode = Field(sa_column=Column(Enum(BiddingMode)))
    process_number: str

    items: Optional[list["Item"]] = Relationship(
        back_populates="bidding",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )


class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    code: str = Field(nullable=False) # New field
    name: str
    desc: str | None = Field(default=None)
    unit: str = Field(nullable=False)
    quantity: float
    notes: str | None = Field(default=None)

    bidding_id: int | None = Field(
        foreign_key="bidding.id", nullable=False, ondelete="CASCADE"
    )

    bidding: Bidding | None = Relationship(back_populates="items")
    suppliers: Optional[list["Supplier"]] = Relationship(
        back_populates="items", link_model=Quote
    )
    bidders: Optional[list["Bidder"]] = Relationship(
        back_populates="items", link_model=Bid
    )


class Supplier(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    name: str = Field(unique=True)
    website: str | None = Field(default=None, unique=True)
    email: str | None = Field(default=None, unique=True)
    phone: str | None = Field(default=None, unique=True)
    desc: str | None = Field(default=None)

    items: Optional[list["Item"]] = Relationship(
        back_populates="suppliers", link_model=Quote
    )


class Bidder(SQLModel, table=True):  # Renamed class
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, default=datetime.now())
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, default=datetime.now(), onupdate=datetime.now()),
    )

    name: str = Field(unique=True)
    website: str | None = Field(default=None, unique=True)
    email: str | None = Field(default=None, unique=True)
    phone: str | None = Field(default=None, unique=True)
    desc: str | None = Field(default=None)

    items: Optional[list["Item"]] = Relationship(
        back_populates="bidders", link_model=Bid
    )
