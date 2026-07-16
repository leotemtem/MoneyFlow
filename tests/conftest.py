"""
Shared pytest fixtures for MoneyFlow tests.
Run the full suite with:  pytest tests/ -v
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Make the src/ layout importable even without an editable install.
SRC = Path(__file__).parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ---------------------------------------------------------------------------
# DataFrame fixtures
# ---------------------------------------------------------------------------


def _make_subscription_df() -> pd.DataFrame:
    """
    A synthetic statement with:
     - Netflix  (monthly, ~£15.99)
     - Spotify  (monthly, ~£11.99)
     - Adobe    (monthly, ~£54.98)
     - An annual payment for NordVPN
     - Some one-off transactions
    """
    rows = []

    # Netflix – 6 monthly payments
    for m in range(1, 7):
        rows.append(
            {
                "Date": f"2025-{m:02d}-05",
                "Description": "NETFLIX MONTHLY",
                "Amount": -15.99,
            }
        )

    # Spotify – 5 monthly payments
    for m in range(1, 6):
        rows.append(
            {
                "Date": f"2025-{m:02d}-12",
                "Description": "SPOTIFY AB",
                "Amount": -11.99,
            }
        )

    # Adobe – 4 monthly payments
    for m in range(1, 5):
        rows.append(
            {
                "Date": f"2025-{m:02d}-20",
                "Description": "ADOBE SYSTEMS",
                "Amount": -54.98,
            }
        )

    # NordVPN – annual (1 payment only → should NOT be detected; need ≥ 2)
    rows.append(
        {
            "Date": "2025-01-10",
            "Description": "NORDVPN ANNUAL",
            "Amount": -59.00,
        }
    )

    # Income
    rows.append({"Date": "2025-01-25", "Description": "SALARY", "Amount": 2500.00})
    rows.append({"Date": "2025-02-25", "Description": "SALARY", "Amount": 2500.00})

    # One-off expense
    rows.append({"Date": "2025-03-14", "Description": "AMAZON ONE OFF", "Amount": -125.00})

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def _make_empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=["Date", "Description", "Amount"])


@pytest.fixture
def subscription_df():
    return _make_subscription_df()


@pytest.fixture
def empty_df():
    return _make_empty_df()


# ---------------------------------------------------------------------------
# Isolated SQLite database fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db(tmp_path):
    """Return a DatabaseHandler backed by a fresh temporary SQLite database (via SQLAlchemy)."""
    from moneyflow.database.handler import DatabaseHandler

    db = DatabaseHandler(database_url=f"sqlite:///{tmp_path}/test.db")
    yield db
    db.close()


# ---------------------------------------------------------------------------
# Auth handler backed by the temp DB
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_handler(tmp_db):
    """AuthHandler that uses the temporary test database."""
    from moneyflow.auth.handler import AuthHandler

    handler = AuthHandler.__new__(AuthHandler)
    handler.db = tmp_db
    return handler
