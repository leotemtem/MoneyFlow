# SPDX-License-Identifier: MIT
"""Database access layer for MoneyFlow.

Manages users, transactions, analysis history and subscriptions through
SQLAlchemy. Uses PostgreSQL in production and SQLite locally/in tests. When no
``database_url`` is supplied it falls back to the configured default (a local
SQLite file), so the application runs with zero configuration.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from moneyflow.config.settings import get_settings
from moneyflow.database.models import (
    AnalysisHistory,
    Base,
    CsvUploadLog,
    Transaction,
    User,
    UserSubscription,
)

logger = logging.getLogger(__name__)


class DatabaseHandler:
    """Handle all database operations using SQLAlchemy (PostgreSQL or SQLite)."""

    def __init__(self, database_url: str | None = None):
        if database_url is None:
            database_url = get_settings().database_url
        # Heroku / Railway use the legacy 'postgres://' scheme.
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        self.engine = create_engine(database_url, pool_pre_ping=True)
        self._Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self._initialize_database()

    def _initialize_database(self):
        """Create tables and apply additive schema updates for legacy DBs."""
        Base.metadata.create_all(self.engine)
        self._apply_schema_updates()

    def _apply_schema_updates(self):
        """Apply safe, additive schema updates without dropping existing data."""
        with self.engine.begin() as connection:
            inspector = inspect(connection)

            if not inspector.has_table("users"):
                return

            existing_columns = {col["name"] for col in inspector.get_columns("users")}

            if "email" not in existing_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))

            if "employment_status" not in existing_columns:
                connection.execute(
                    text("ALTER TABLE users ADD COLUMN employment_status VARCHAR(50)")
                )

            if "created_at" not in existing_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP"))
                connection.execute(
                    text("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
                )

            if "last_login" not in existing_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN last_login TIMESTAMP"))

    def _session(self) -> Session:
        return self._Session()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    # ============= USER MANAGEMENT =============

    def register_user(
        self, username: str, password: str, email: str = "", employment_status: str = ""
    ) -> tuple[bool, str]:
        with self._session() as session:
            try:
                session.add(
                    User(
                        username=username,
                        password_hash=self._hash_password(password),
                        email=email or None,
                        employment_status=employment_status or None,
                    )
                )
                session.commit()
                return True, "Registration successful! Please login."
            except IntegrityError:
                session.rollback()
                return False, "Username already exists"
            except Exception as e:
                session.rollback()
                return False, f"Registration failed: {str(e)}"

    def authenticate_user(self, username: str, password: str) -> tuple[bool, str]:
        with self._session() as session:
            try:
                user = session.scalar(
                    select(User).where(
                        User.username == username,
                        User.password_hash == self._hash_password(password),
                    )
                )
                if user:
                    user.last_login = datetime.utcnow()
                    session.commit()
                    return True, "Login successful!"
                return False, "Invalid username or password"
            except Exception as e:
                session.rollback()
                return False, f"Authentication failed: {str(e)}"

    def get_user_id(self, username: str) -> int | None:
        with self._session() as session:
            try:
                return session.scalar(select(User.id).where(User.username == username))
            except Exception:
                return None

    def get_user_info(self, username: str) -> dict:
        with self._session() as session:
            try:
                user = session.scalar(select(User).where(User.username == username))
                if user:
                    return {
                        "username": user.username,
                        "email": user.email,
                        "employment_status": user.employment_status,
                        "created_at": str(user.created_at),
                        "last_login": str(user.last_login),
                    }
                return {}
            except Exception:
                return {}

    def user_exists(self, username: str) -> bool:
        return self.get_user_id(username) is not None

    def change_password(self, username: str, new_password_hash: str) -> tuple[bool, str]:
        with self._session() as session:
            try:
                user = session.scalar(select(User).where(User.username == username))
                if not user:
                    return False, "User not found"
                user.password_hash = new_password_hash
                session.commit()
                return True, "Password changed successfully!"
            except Exception as e:
                session.rollback()
                return False, f"Failed to change password: {str(e)}"

    # ============= TRANSACTION MANAGEMENT =============

    def save_transactions(self, username: str, df: pd.DataFrame) -> tuple[bool, str]:
        user_id = self.get_user_id(username)
        if not user_id:
            return False, "User not found"

        with self._session() as session:
            try:
                upload_date = datetime.utcnow()
                session.add_all(
                    [
                        Transaction(
                            user_id=user_id,
                            upload_date=upload_date,
                            transaction_date=pd.to_datetime(row["Date"]).date(),
                            description=row["Description"],
                            amount=row["Amount"],
                            transaction_type=row.get("Type", ""),
                            category=row.get("Category", "Other"),
                        )
                        for _, row in df.iterrows()
                    ]
                )
                session.commit()
                return True, f"Saved {len(df)} transactions"
            except Exception as e:
                session.rollback()
                return False, f"Failed to save transactions: {str(e)}"

    def get_user_transactions(self, username: str, limit: int | None = None) -> pd.DataFrame:
        user_id = self.get_user_id(username)
        if not user_id:
            return pd.DataFrame()
        try:
            stmt = (
                select(
                    Transaction.transaction_date.label("Date"),
                    Transaction.description.label("Description"),
                    Transaction.amount.label("Amount"),
                    Transaction.transaction_type.label("Type"),
                    Transaction.category.label("Category"),
                    Transaction.upload_date,
                )
                .where(Transaction.user_id == user_id)
                .order_by(Transaction.transaction_date.desc())
            )
            if limit:
                stmt = stmt.limit(int(limit))
            with self.engine.connect() as conn:
                df = pd.read_sql(stmt, conn)
            if not df.empty:
                df["Date"] = pd.to_datetime(df["Date"])
            return df
        except Exception as e:
            logger.warning("Error fetching transactions: %s", e)
            return pd.DataFrame()

    def delete_user_transactions(self, username: str) -> tuple[bool, str]:
        user_id = self.get_user_id(username)
        if not user_id:
            return False, "User not found"

        with self._session() as session:
            try:
                session.query(Transaction).filter_by(user_id=user_id).delete()
                session.commit()
                return True, "All transactions deleted"
            except Exception as e:
                session.rollback()
                return False, f"Failed to delete transactions: {str(e)}"

    def get_transaction_count(self, username: str) -> int:
        user_id = self.get_user_id(username)
        if not user_id:
            return 0
        with self._session() as session:
            try:
                return (
                    session.scalar(
                        select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
                    )
                    or 0
                )
            except Exception:
                return 0

    # ============= CSV RATE LIMITING =============

    DAILY_CSV_LIMIT = 10

    def check_upload_rate_limit(self, username: str) -> tuple[bool, int, int]:
        """Check whether the user can upload another CSV today.

        Returns:
            (allowed, used, limit) — allowed is True when under the daily cap.
        """
        user_id = self.get_user_id(username)
        if not user_id:
            return False, 0, self.DAILY_CSV_LIMIT
        window_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        with self._session() as session:
            try:
                used = (
                    session.scalar(
                        select(func.count(CsvUploadLog.id)).where(
                            CsvUploadLog.user_id == user_id,
                            CsvUploadLog.uploaded_at >= window_start,
                        )
                    )
                    or 0
                )
                return used < self.DAILY_CSV_LIMIT, used, self.DAILY_CSV_LIMIT
            except Exception:
                return True, 0, self.DAILY_CSV_LIMIT

    def record_csv_upload(self, username: str) -> None:
        """Record a CSV analysis submission for the given user."""
        user_id = self.get_user_id(username)
        if not user_id:
            return
        with self._session() as session:
            try:
                session.add(CsvUploadLog(user_id=user_id, uploaded_at=datetime.utcnow()))
                session.commit()
            except Exception as e:
                session.rollback()
                logger.warning("Error recording CSV upload: %s", e)

    # ============= ANALYSIS HISTORY =============

    def save_analysis(self, username: str, query: str, response: str) -> bool:
        user_id = self.get_user_id(username)
        if not user_id:
            return False
        with self._session() as session:
            try:
                session.add(AnalysisHistory(user_id=user_id, query=query, response=response))
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logger.warning("Error saving analysis: %s", e)
                return False

    def get_analysis_history(self, username: str, limit: int = 10) -> list[dict]:
        user_id = self.get_user_id(username)
        if not user_id:
            return []
        with self._session() as session:
            try:
                rows = session.scalars(
                    select(AnalysisHistory)
                    .where(AnalysisHistory.user_id == user_id)
                    .order_by(AnalysisHistory.timestamp.desc())
                    .limit(limit)
                ).all()
                return [
                    {"timestamp": str(r.timestamp), "query": r.query, "response": r.response}
                    for r in rows
                ]
            except Exception as e:
                logger.warning("Error fetching analysis history: %s", e)
                return []

    # ============= SUBSCRIPTION MANAGEMENT =============

    def save_subscriptions(self, username: str, subscriptions: list) -> tuple[bool, str]:
        user_id = self.get_user_id(username)
        if not user_id:
            return False, "User not found"

        with self._session() as session:
            try:
                for sub in subscriptions:
                    existing = session.scalar(
                        select(UserSubscription).where(
                            UserSubscription.user_id == user_id,
                            UserSubscription.description == sub["description"],
                        )
                    )
                    if existing:
                        existing.display_name = sub["name"]
                        existing.category = sub["category"]
                        existing.frequency = sub["frequency"]
                        existing.avg_monthly_cost = sub["avg_monthly_cost"]
                        existing.annual_cost = sub["annual_cost"]
                        existing.last_payment = sub["last_payment"]
                        existing.next_estimated = sub["next_estimated"]
                        existing.occurrences = sub["occurrences"]
                        existing.detected_at = datetime.utcnow()
                    else:
                        session.add(
                            UserSubscription(
                                user_id=user_id,
                                description=sub["description"],
                                display_name=sub["name"],
                                category=sub["category"],
                                frequency=sub["frequency"],
                                avg_monthly_cost=sub["avg_monthly_cost"],
                                annual_cost=sub["annual_cost"],
                                last_payment=sub["last_payment"],
                                next_estimated=sub["next_estimated"],
                                occurrences=sub["occurrences"],
                            )
                        )
                session.commit()
                return True, f"Saved {len(subscriptions)} subscriptions"
            except Exception as e:
                session.rollback()
                return False, f"Failed to save subscriptions: {str(e)}"

    def get_user_subscriptions(self, username: str, active_only: bool = True) -> list[dict]:
        user_id = self.get_user_id(username)
        if not user_id:
            return []
        with self._session() as session:
            try:
                stmt = select(UserSubscription).where(UserSubscription.user_id == user_id)
                if active_only:
                    stmt = stmt.where(UserSubscription.is_active.is_(True))
                stmt = stmt.order_by(UserSubscription.avg_monthly_cost.desc())
                rows = session.scalars(stmt).all()
                return [
                    {
                        "description": r.description,
                        "name": r.display_name,
                        "category": r.category,
                        "frequency": r.frequency,
                        "avg_monthly_cost": r.avg_monthly_cost,
                        "annual_cost": r.annual_cost,
                        "last_payment": r.last_payment,
                        "next_estimated": r.next_estimated,
                        "occurrences": r.occurrences,
                        "is_active": r.is_active,
                        "notes": r.notes,
                        "detected_at": str(r.detected_at),
                    }
                    for r in rows
                ]
            except Exception as e:
                logger.warning("Error fetching subscriptions: %s", e)
                return []

    def toggle_subscription_active(
        self, username: str, description: str, is_active: bool
    ) -> tuple[bool, str]:
        user_id = self.get_user_id(username)
        if not user_id:
            return False, "User not found"

        with self._session() as session:
            try:
                sub = session.scalar(
                    select(UserSubscription).where(
                        UserSubscription.user_id == user_id,
                        UserSubscription.description == description,
                    )
                )
                if not sub:
                    return False, "Subscription not found"
                sub.is_active = is_active
                session.commit()
                status = "activated" if is_active else "deactivated"
                return True, f"Subscription {status}"
            except Exception as e:
                session.rollback()
                return False, f"Failed to update subscription: {str(e)}"

    def update_subscription_notes(
        self, username: str, description: str, notes: str
    ) -> tuple[bool, str]:
        user_id = self.get_user_id(username)
        if not user_id:
            return False, "User not found"

        with self._session() as session:
            try:
                sub = session.scalar(
                    select(UserSubscription).where(
                        UserSubscription.user_id == user_id,
                        UserSubscription.description == description,
                    )
                )
                if not sub:
                    return False, "Subscription not found"
                sub.notes = notes
                session.commit()
                return True, "Notes saved"
            except Exception as e:
                session.rollback()
                return False, f"Failed to update notes: {str(e)}"

    def get_subscription_count(self, username: str) -> int:
        user_id = self.get_user_id(username)
        if not user_id:
            return 0
        with self._session() as session:
            try:
                return (
                    session.scalar(
                        select(func.count(UserSubscription.id)).where(
                            UserSubscription.user_id == user_id,
                            UserSubscription.is_active.is_(True),
                        )
                    )
                    or 0
                )
            except Exception:
                return 0

    def close(self):
        """Dispose engine connection pool."""
        self.engine.dispose()
