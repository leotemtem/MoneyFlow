# SPDX-License-Identifier: MIT
"""SQLAlchemy ORM models for MoneyFlow.

The same models run against PostgreSQL in production and SQLite in tests/local
development, so only portable column types and constructs are used here.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


EMPLOYMENT_STATUSES = [
    "Student",
    "Full-time Employed",
    "Part-time Employed",
    "Self-employed",
    "Business Owner",
    "Unemployed",
    "Retired",
]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    employment_status: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    transaction_date = Column(Date, nullable=False)
    description = Column(Text)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50))
    category = Column(String(100))

    __table_args__ = (
        Index("idx_transactions_user", "user_id"),
        Index("idx_transactions_date", "transaction_date"),
    )


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    query = Column(Text, nullable=False)
    response = Column(Text)

    __table_args__ = (Index("idx_analysis_user", "user_id"),)


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    budget_limit = Column(Float)
    currency = Column(String(10), default="GBP")
    notification_enabled = Column(Boolean, default=True)


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), default="Other")
    frequency: Mapped[str | None] = mapped_column(String(50), default="Monthly")
    avg_monthly_cost: Mapped[float] = mapped_column(Float, nullable=False)
    annual_cost: Mapped[float] = mapped_column(Float, nullable=False)
    last_payment: Mapped[str | None] = mapped_column(String(50))
    next_estimated: Mapped[str | None] = mapped_column(String(50))
    occurrences: Mapped[int | None] = mapped_column(Integer, default=1)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class CsvUploadLog(Base):
    """Tracks per-user CSV analysis submissions for rate limiting."""

    __tablename__ = "csv_upload_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("idx_csv_upload_user", "user_id"),)
