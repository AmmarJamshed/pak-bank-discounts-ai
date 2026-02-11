from datetime import date

from sqlalchemy import (
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Bank(Base):
    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    website: Mapped[str] = mapped_column(String(500), nullable=False)

    cards: Mapped[list["Card"]] = relationship(back_populates="bank")


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("banks.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[str] = mapped_column(String(100), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)

    bank: Mapped["Bank"] = relationship(back_populates="cards")
    discounts: Mapped[list["Discount"]] = relationship(back_populates="card")

    __table_args__ = (UniqueConstraint("bank_id", "name", name="uq_cards_bank_name"),)


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(150), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    discounts: Mapped[list["Discount"]] = relationship(back_populates="merchant")


class Discount(Base):
    __tablename__ = "discounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), nullable=False)
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False)
    conditions: Mapped[str] = mapped_column(Text, nullable=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date] = mapped_column(Date, nullable=True)

    merchant: Mapped["Merchant"] = relationship(back_populates="discounts")
    card: Mapped["Card"] = relationship(back_populates="discounts")

    __table_args__ = (
        UniqueConstraint(
            "merchant_id",
            "card_id",
            "discount_percent",
            "valid_from",
            "valid_to",
            name="uq_discount_unique",
        ),
    )
