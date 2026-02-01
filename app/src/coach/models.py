# app/src/models.py
from sqlalchemy.ext.asyncio import AsyncAttrs  # lazily load async relationships
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import Date, String, ForeignKey, Text, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class User(AsyncAttrs, Base):
    __tablename__ = "users"

    # mapped_column handles the SQL definition.
    id_: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)

    # Optional[str] translates to a nullable SQL column
    financial_goals: Mapped[Optional[str]] = mapped_column(Text)

    # server_default needs to be passed to mapped_column
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # One-to-Many Relationship
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id_}, username='{self.username}')>"


class Transaction(AsyncAttrs, Base):
    __tablename__ = "transactions"

    id_: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign Key
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id_"))

    # Use Decimal for monetary values
    amount: Mapped[Decimal] = mapped_column(nullable=False)
    merchant: Mapped[str] = mapped_column(String(100))
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Nullable fields for AI analysis
    category: Mapped[Optional[str]] = mapped_column(String(50))
    is_subscription: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Many-to-One Relationship
    owner: Mapped["User"] = relationship("User", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id_}, merchant='{self.merchant}', amount={self.amount})>"
