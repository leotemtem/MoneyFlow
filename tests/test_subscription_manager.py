"""
Unit tests for SubscriptionManager
"""

import pandas as pd

from moneyflow.analytics.subscriptions import (
    SubscriptionManager,
    _frequency_label,
    _normalise_description,
)

# ---------------------------------------------------------------------------
# Helper / unit tests
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_normalise_strips_punctuation(self):
        assert _normalise_description("Netflix!") == "netflix"

    def test_normalise_lowercases(self):
        assert _normalise_description("SPOTIFY AB") == "spotify ab"

    def test_normalise_removes_special_chars(self):
        assert _normalise_description("ADOBE*SYSTEMS") == "adobe systems"

    def test_frequency_monthly(self):
        assert _frequency_label(30) == "Monthly"

    def test_frequency_quarterly(self):
        assert _frequency_label(91) == "Quarterly"

    def test_frequency_annual(self):
        assert _frequency_label(365) == "Annual"

    def test_frequency_other(self):
        label = _frequency_label(14)
        assert "14" in label


# ---------------------------------------------------------------------------
# SubscriptionManager.detect_subscriptions
# ---------------------------------------------------------------------------


class TestDetectSubscriptions:
    def test_detects_netflix(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        names = [s["name"] for s in subs]
        assert "Netflix" in names

    def test_detects_spotify(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        names = [s["name"] for s in subs]
        assert "Spotify" in names

    def test_detects_adobe(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        names = [s["name"] for s in subs]
        assert "Adobe Creative" in names

    def test_single_occurrence_not_detected(self, subscription_df):
        """NordVPN appears only once → should not be returned."""
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        names = [s["name"] for s in subs]
        assert "NordVPN" not in names

    def test_income_not_included(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        # SALARY appears twice but is income (positive amount)
        names_lower = [s["name"].lower() for s in subs]
        assert not any("salary" in n for n in names_lower)

    def test_empty_dataframe_returns_empty(self, empty_df):
        mgr = SubscriptionManager(empty_df)
        assert mgr.detect_subscriptions() == []

    def test_result_sorted_by_monthly_cost(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        costs = [s["avg_monthly_cost"] for s in subs]
        assert costs == sorted(costs, reverse=True)

    def test_subscription_has_required_keys(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        required = {
            "name",
            "description",
            "category",
            "known_service",
            "frequency",
            "occurrences",
            "avg_amount",
            "avg_monthly_cost",
            "annual_cost",
            "first_payment",
            "last_payment",
            "next_estimated",
            "all_amounts",
        }
        for sub in subs:
            assert required.issubset(sub.keys()), f"Missing keys in: {sub}"

    def test_monthly_frequency_label(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        for sub in subs:
            assert sub["frequency"] == "Monthly"

    def test_known_service_flag(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        netflix = next(s for s in subs if s["name"] == "Netflix")
        assert netflix["known_service"] is True

    def test_annual_cost_is_12x_monthly(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        for sub in subs:
            expected = round(sub["avg_monthly_cost"] * 12, 2)
            assert abs(sub["annual_cost"] - expected) < 0.02


# ---------------------------------------------------------------------------
# SubscriptionManager.get_summary
# ---------------------------------------------------------------------------


class TestGetSummary:
    def test_empty_subscriptions(self):
        mgr = SubscriptionManager(pd.DataFrame(columns=["Date", "Description", "Amount"]))
        summary = mgr.get_summary([])
        assert summary["count"] == 0
        assert summary["total_monthly"] == 0.0
        assert summary["total_annual"] == 0.0

    def test_count_matches(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        summary = mgr.get_summary(subs)
        assert summary["count"] == len(subs)

    def test_total_monthly_equals_sum(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        summary = mgr.get_summary(subs)
        expected = round(sum(s["avg_monthly_cost"] for s in subs), 2)
        assert abs(summary["total_monthly"] - expected) < 0.01

    def test_most_expensive_present(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        summary = mgr.get_summary(subs)
        assert summary["most_expensive"] is not None
        assert summary["most_expensive"]["name"] == "Adobe Creative"

    def test_by_category_keys(self, subscription_df):
        mgr = SubscriptionManager(subscription_df)
        subs = mgr.detect_subscriptions()
        summary = mgr.get_summary(subs)
        assert isinstance(summary["by_category"], dict)
        for cat, info in summary["by_category"].items():
            assert "count" in info
            assert "monthly_cost" in info


# ---------------------------------------------------------------------------
# SubscriptionManager.get_cancellation_candidates
# ---------------------------------------------------------------------------


class TestCancellationCandidates:
    def _make_old_subscription_df(self):
        """Netflix paid 5 months ago, Spotify paid last month."""
        rows = []

        # Netflix – last payment 5 months ago
        for m in [1, 2, 3]:
            rows.append(
                {
                    "Date": f"2025-{m:02d}-05",
                    "Description": "NETFLIX",
                    "Amount": -15.99,
                }
            )

        # Spotify – recent (last 2 months, relative to max date in dataset)
        for m in [1, 2, 3, 8, 9]:
            rows.append(
                {
                    "Date": f"2025-{m:02d}-12",
                    "Description": "SPOTIFY AB",
                    "Amount": -11.99,
                }
            )

        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"])
        return df

    def test_inactive_subscription_flagged(self):
        df = self._make_old_subscription_df()
        mgr = SubscriptionManager(df)
        subs = mgr.detect_subscriptions()
        candidates = mgr.get_cancellation_candidates(subs, months_inactive=4)
        names = [c["name"] for c in candidates]
        assert "Netflix" in names

    def test_active_subscription_not_flagged(self):
        df = self._make_old_subscription_df()
        mgr = SubscriptionManager(df)
        subs = mgr.detect_subscriptions()
        # With 2 months threshold Spotify should be fine (last payment in month 9)
        candidates = mgr.get_cancellation_candidates(subs, months_inactive=2)
        names = [c["name"] for c in candidates]
        assert "Spotify" not in names

    def test_candidate_has_months_since_last(self):
        df = self._make_old_subscription_df()
        mgr = SubscriptionManager(df)
        subs = mgr.detect_subscriptions()
        candidates = mgr.get_cancellation_candidates(subs, months_inactive=4)
        for c in candidates:
            assert "months_since_last" in c
            assert c["months_since_last"] > 0
