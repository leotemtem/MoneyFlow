"""
Integration tests for DatabaseHandler
All tests use an isolated temporary SQLite database.
"""

import pandas as pd
import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------


class TestUserManagement:
    def test_register_and_authenticate(self, tmp_db):
        ok, _ = tmp_db.register_user("alice", "pass123", "alice@test.com")
        assert ok
        ok, _ = tmp_db.authenticate_user("alice", "pass123")
        assert ok

    def test_duplicate_username_rejected(self, tmp_db):
        tmp_db.register_user("bob", "pass123")
        ok, msg = tmp_db.register_user("bob", "different123")
        assert not ok

    def test_wrong_password_rejected(self, tmp_db):
        tmp_db.register_user("carol", "correct123")
        ok, _ = tmp_db.authenticate_user("carol", "wrong123")
        assert not ok

    def test_user_exists(self, tmp_db):
        assert not tmp_db.user_exists("ghost")
        tmp_db.register_user("dave", "pass123")
        assert tmp_db.user_exists("dave")

    def test_get_user_id(self, tmp_db):
        tmp_db.register_user("eve", "pass123")
        uid = tmp_db.get_user_id("eve")
        assert isinstance(uid, int)
        assert uid > 0

    def test_get_user_info_fields(self, tmp_db):
        tmp_db.register_user("frank", "pass123", "frank@test.com")
        info = tmp_db.get_user_info("frank")
        assert info["username"] == "frank"
        assert info["email"] == "frank@test.com"
        assert "password_hash" not in info

    def test_change_password(self, tmp_db):
        tmp_db.register_user("grace", "old_pass1")
        import hashlib

        new_hash = hashlib.sha256(b"new_pass2").hexdigest()
        ok, _ = tmp_db.change_password("grace", new_hash)
        assert ok
        ok, _ = tmp_db.authenticate_user("grace", "new_pass2")
        assert ok


# ---------------------------------------------------------------------------
# Transaction management
# ---------------------------------------------------------------------------


class TestTransactionManagement:
    def _sample_df(self):
        return pd.DataFrame(
            {
                "Date": ["2025-01-05", "2025-01-10", "2025-01-15"],
                "Description": ["Salary", "Tesco", "Netflix"],
                "Amount": [2500.00, -55.00, -15.99],
                "Type": ["Income", "Expense", "Expense"],
                "Category": ["Income", "Groceries", "Entertainment"],
            }
        )

    def test_save_and_count(self, tmp_db):
        tmp_db.register_user("henry", "pass123")
        ok, msg = tmp_db.save_transactions("henry", self._sample_df())
        assert ok
        assert tmp_db.get_transaction_count("henry") == 3

    def test_load_transactions_returns_dataframe(self, tmp_db):
        tmp_db.register_user("iris", "pass123")
        tmp_db.save_transactions("iris", self._sample_df())
        df = tmp_db.get_user_transactions("iris")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

    def test_transactions_are_isolated_by_user(self, tmp_db):
        tmp_db.register_user("owner", "pass123")
        tmp_db.register_user("other", "pass123")

        tmp_db.save_transactions("owner", self._sample_df())

        owner_df = tmp_db.get_user_transactions("owner")
        other_df = tmp_db.get_user_transactions("other")

        assert len(owner_df) == 3
        assert other_df.empty

    def test_delete_transactions(self, tmp_db):
        tmp_db.register_user("jack", "pass123")
        tmp_db.save_transactions("jack", self._sample_df())
        ok, _ = tmp_db.delete_user_transactions("jack")
        assert ok
        assert tmp_db.get_transaction_count("jack") == 0

    def test_unknown_user_save_fails(self, tmp_db):
        ok, msg = tmp_db.save_transactions("ghost", self._sample_df())
        assert not ok


# ---------------------------------------------------------------------------
# Subscription management
# ---------------------------------------------------------------------------


class TestSubscriptionManagement:
    def _sample_subscriptions(self):
        return [
            {
                "description": "NETFLIX MONTHLY",
                "name": "Netflix",
                "category": "Streaming (Video)",
                "frequency": "Monthly",
                "avg_monthly_cost": 15.99,
                "annual_cost": 191.88,
                "last_payment": "2025-06-05",
                "next_estimated": "2025-07-05",
                "occurrences": 6,
            },
            {
                "description": "SPOTIFY AB",
                "name": "Spotify",
                "category": "Streaming (Music)",
                "frequency": "Monthly",
                "avg_monthly_cost": 11.99,
                "annual_cost": 143.88,
                "last_payment": "2025-05-12",
                "next_estimated": "2025-06-12",
                "occurrences": 5,
            },
        ]

    def test_save_subscriptions(self, tmp_db):
        tmp_db.register_user("karen", "pass123")
        ok, msg = tmp_db.save_subscriptions("karen", self._sample_subscriptions())
        assert ok
        assert "2" in msg

    def test_load_subscriptions(self, tmp_db):
        tmp_db.register_user("leo", "pass123")
        tmp_db.save_subscriptions("leo", self._sample_subscriptions())
        subs = tmp_db.get_user_subscriptions("leo")
        assert len(subs) == 2
        names = [s["name"] for s in subs]
        assert "Netflix" in names
        assert "Spotify" in names

    def test_subscriptions_are_isolated_by_user(self, tmp_db):
        tmp_db.register_user("owner", "pass123")
        tmp_db.register_user("other", "pass123")

        tmp_db.save_subscriptions("owner", self._sample_subscriptions())

        assert tmp_db.get_subscription_count("owner") == 2
        assert tmp_db.get_user_subscriptions("other") == []

    def test_subscription_count(self, tmp_db):
        tmp_db.register_user("mia", "pass123")
        tmp_db.save_subscriptions("mia", self._sample_subscriptions())
        assert tmp_db.get_subscription_count("mia") == 2

    def test_toggle_subscription_inactive(self, tmp_db):
        tmp_db.register_user("nina", "pass123")
        tmp_db.save_subscriptions("nina", self._sample_subscriptions())
        ok, _ = tmp_db.toggle_subscription_active("nina", "NETFLIX MONTHLY", False)
        assert ok
        # Active-only query should return 1 now
        assert tmp_db.get_subscription_count("nina") == 1

    def test_toggle_subscription_back_active(self, tmp_db):
        tmp_db.register_user("oliver", "pass123")
        tmp_db.save_subscriptions("oliver", self._sample_subscriptions())
        tmp_db.toggle_subscription_active("oliver", "NETFLIX MONTHLY", False)
        tmp_db.toggle_subscription_active("oliver", "NETFLIX MONTHLY", True)
        assert tmp_db.get_subscription_count("oliver") == 2

    def test_upsert_updates_existing(self, tmp_db):
        tmp_db.register_user("petra", "pass123")
        tmp_db.save_subscriptions("petra", self._sample_subscriptions())
        # Save again with updated cost
        updated = self._sample_subscriptions()
        updated[0]["avg_monthly_cost"] = 17.99
        tmp_db.save_subscriptions("petra", updated)
        subs = tmp_db.get_user_subscriptions("petra")
        netflix = next(s for s in subs if s["name"] == "Netflix")
        assert netflix["avg_monthly_cost"] == 17.99
        # Should not create duplicates
        assert tmp_db.get_subscription_count("petra") == 2

    def test_update_notes(self, tmp_db):
        tmp_db.register_user("quinn", "pass123")
        tmp_db.save_subscriptions("quinn", self._sample_subscriptions())
        ok, _ = tmp_db.update_subscription_notes("quinn", "NETFLIX MONTHLY", "Consider cancelling")
        assert ok
        subs = tmp_db.get_user_subscriptions("quinn")
        netflix = next(s for s in subs if s["name"] == "Netflix")
        assert netflix["notes"] == "Consider cancelling"

    def test_unknown_user_save_fails(self, tmp_db):
        ok, _ = tmp_db.save_subscriptions("ghost", self._sample_subscriptions())
        assert not ok


# ---------------------------------------------------------------------------
# Analysis history
# ---------------------------------------------------------------------------


class TestAnalysisHistory:
    def test_save_and_retrieve(self, tmp_db):
        tmp_db.register_user("rachel", "pass123")
        saved = tmp_db.save_analysis("rachel", "Test query", "Test response")
        assert saved
        history = tmp_db.get_analysis_history("rachel")
        assert len(history) == 1
        assert history[0]["query"] == "Test query"

    def test_analysis_history_is_isolated_by_user(self, tmp_db):
        tmp_db.register_user("owner", "pass123")
        tmp_db.register_user("other", "pass123")

        assert tmp_db.save_analysis("owner", "Private query", "Private response")

        assert len(tmp_db.get_analysis_history("owner")) == 1
        assert tmp_db.get_analysis_history("other") == []

    def test_limit_respected(self, tmp_db):
        tmp_db.register_user("sam", "pass123")
        for i in range(15):
            tmp_db.save_analysis("sam", f"query {i}", f"response {i}")
        history = tmp_db.get_analysis_history("sam", limit=5)
        assert len(history) == 5
