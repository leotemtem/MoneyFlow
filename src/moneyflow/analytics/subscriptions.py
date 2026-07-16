"""
Subscription Manager
Detects, categorises, and tracks recurring subscription payments from bank statement data.
"""

import re
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Known subscription services – keyword → (display_name, category, typical £/month)
# ---------------------------------------------------------------------------
KNOWN_SUBSCRIPTIONS: dict[str, tuple[str, str, float]] = {
    # Streaming – Video
    "netflix": ("Netflix", "Streaming (Video)", 15.99),
    "disney": ("Disney+", "Streaming (Video)", 11.99),
    "amazon prime": ("Amazon Prime", "Streaming (Video)", 8.99),
    "prime video": ("Amazon Prime", "Streaming (Video)", 8.99),
    "now tv": ("NOW TV", "Streaming (Video)", 9.99),
    "apple tv": ("Apple TV+", "Streaming (Video)", 8.99),
    "paramount": ("Paramount+", "Streaming (Video)", 6.99),
    "hulu": ("Hulu", "Streaming (Video)", 7.99),
    "hbo": ("HBO Max", "Streaming (Video)", 15.99),
    "peacock": ("Peacock", "Streaming (Video)", 5.99),
    "mubi": ("MUBI", "Streaming (Video)", 12.99),
    "bfi player": ("BFI Player", "Streaming (Video)", 4.99),
    # Streaming – Music
    "spotify": ("Spotify", "Streaming (Music)", 11.99),
    "apple music": ("Apple Music", "Streaming (Music)", 10.99),
    "tidal": ("Tidal", "Streaming (Music)", 11.99),
    "amazon music": ("Amazon Music", "Streaming (Music)", 10.99),
    "deezer": ("Deezer", "Streaming (Music)", 11.99),
    "youtube premium": ("YouTube Premium", "Streaming (Music)", 13.99),
    "youtube music": ("YouTube Premium", "Streaming (Music)", 13.99),
    "soundcloud": ("SoundCloud", "Streaming (Music)", 9.99),
    # Cloud Storage / Productivity
    "icloud": ("iCloud", "Cloud / Productivity", 2.99),
    "google one": ("Google One", "Cloud / Productivity", 1.99),
    "google storage": ("Google One", "Cloud / Productivity", 1.99),
    "dropbox": ("Dropbox", "Cloud / Productivity", 9.99),
    "microsoft 365": ("Microsoft 365", "Cloud / Productivity", 99.00),
    "office 365": ("Microsoft 365", "Cloud / Productivity", 9.99),
    "onedrive": ("Microsoft 365", "Cloud / Productivity", 1.99),
    "adobe": ("Adobe Creative", "Cloud / Productivity", 54.98),
    "notion": ("Notion", "Cloud / Productivity", 8.00),
    "evernote": ("Evernote", "Cloud / Productivity", 7.99),
    "1password": ("1Password", "Cloud / Productivity", 3.99),
    "lastpass": ("LastPass", "Cloud / Productivity", 3.00),
    # Gaming
    "xbox game pass": ("Xbox Game Pass", "Gaming", 14.99),
    "xbox": ("Xbox", "Gaming", 14.99),
    "playstation plus": ("PlayStation Plus", "Gaming", 13.99),
    "playstation": ("PlayStation", "Gaming", 13.99),
    "nintendo": ("Nintendo Online", "Gaming", 3.99),
    "ea play": ("EA Play", "Gaming", 3.99),
    "ubisoft": ("Ubisoft+", "Gaming", 14.99),
    "steam": ("Steam", "Gaming", 0.00),
    "humble bundle": ("Humble Bundle", "Gaming", 12.00),
    # News & Reading
    "times": ("The Times", "News & Reading", 26.00),
    "guardian": ("The Guardian", "News & Reading", 10.00),
    "financial times": ("Financial Times", "News & Reading", 39.99),
    "the economist": ("The Economist", "News & Reading", 22.00),
    "new york times": ("New York Times", "News & Reading", 17.00),
    "audible": ("Audible", "News & Reading", 7.99),
    "kindle unlimited": ("Kindle Unlimited", "News & Reading)", 8.99),
    "readly": ("Readly", "News & Reading", 9.99),
    # Fitness & Wellbeing
    "gym": ("Gym Membership", "Fitness", 40.00),
    "peloton": ("Peloton", "Fitness", 44.00),
    "headspace": ("Headspace", "Fitness", 12.99),
    "calm": ("Calm", "Fitness", 14.99),
    "strava": ("Strava", "Fitness", 5.99),
    "fiit": ("Fiit", "Fitness", 20.00),
    "noom": ("Noom", "Fitness", 59.00),
    # Utilities / Services
    "vpn": ("VPN Service", "Utilities", 5.00),
    "nordvpn": ("NordVPN", "Utilities", 4.92),
    "expressvpn": ("ExpressVPN", "Utilities", 12.95),
    "antivirus": ("Antivirus", "Utilities", 3.00),
    "norton": ("Norton", "Utilities", 8.33),
    "mcafee": ("McAfee", "Utilities", 6.99),
    # Food & Shopping
    "amazon": ("Amazon", "Shopping", 8.99),
    "deliveroo": ("Deliveroo Plus", "Food & Shopping", 3.99),
    "just eat": ("Just Eat", "Food & Shopping", 3.99),
    "graze": ("Graze", "Food & Shopping", 4.99),
    "hello fresh": ("HelloFresh", "Food & Shopping", 5.99),
    "gousto": ("Gousto", "Food & Shopping", 5.99),
}

SUBSCRIPTION_CATEGORIES = sorted({v[1] for v in KNOWN_SUBSCRIPTIONS.values()})

# Frequency thresholds in days
MONTHLY_MIN = 20
MONTHLY_MAX = 45
QUARTERLY_MIN = 80
QUARTERLY_MAX = 100
ANNUAL_MIN = 330
ANNUAL_MAX = 400


def _normalise_description(desc: str) -> str:
    """Lower-case, strip punctuation for fuzzy matching."""
    return re.sub(r"[^a-z0-9 ]", " ", str(desc).lower()).strip()


def _frequency_label(avg_days: float) -> str:
    if MONTHLY_MIN <= avg_days <= MONTHLY_MAX:
        return "Monthly"
    if QUARTERLY_MIN <= avg_days <= QUARTERLY_MAX:
        return "Quarterly"
    if ANNUAL_MIN <= avg_days <= ANNUAL_MAX:
        return "Annual"
    return f"Every ~{avg_days:.0f} days"


def _monthly_equivalent(amount: float, freq_label: str) -> float:
    """Convert an amount to its monthly equivalent given frequency."""
    if freq_label == "Annual":
        return round(amount / 12, 2)
    if freq_label == "Quarterly":
        return round(amount / 3, 2)
    return round(amount, 2)


class SubscriptionManager:
    """
    Identify and categorise subscription payments in a bank statement DataFrame.

    The DataFrame must have columns: Date (datetime), Description (str), Amount (float).
    Negative amounts are treated as expenses.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df["Date"] = pd.to_datetime(self.df["Date"])
        self._expenses = self.df[self.df["Amount"] < 0].copy()
        self._expenses["_norm"] = self._expenses["Description"].apply(_normalise_description)
        self._manual_subscriptions: list[dict] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_subscriptions(self) -> list[dict]:
        """
        Scan statement for recurring payments and return a list of subscription dicts.

        Each dict contains:
            name, category, description (raw), frequency, occurrences,
            avg_monthly_cost, annual_cost, last_payment, next_estimated,
            all_amounts, first_payment, known_service (bool)
        """
        groups = self._group_similar_transactions()
        subscriptions = []

        for raw_desc, group_df in groups.items():
            sub = self._analyse_group(raw_desc, group_df)
            if sub is not None:
                subscriptions.append(sub)

        # De-duplicate by name (keep highest occurrence count)
        seen: dict[str, dict] = {}
        for sub in subscriptions:
            key = sub["name"].lower()
            if key not in seen or sub["occurrences"] > seen[key]["occurrences"]:
                seen[key] = sub

        result = list(seen.values())
        return sorted(result, key=lambda x: x["avg_monthly_cost"], reverse=True)

    def get_summary(self, subscriptions: list[dict]) -> dict:
        """Return headline figures for a list of subscriptions."""
        if not subscriptions:
            return {
                "total_monthly": 0.0,
                "total_annual": 0.0,
                "count": 0,
                "by_category": {},
                "most_expensive": None,
            }

        total_monthly = sum(s["avg_monthly_cost"] for s in subscriptions)
        total_annual = sum(s["annual_cost"] for s in subscriptions)

        by_category: dict[str, dict] = {}
        for sub in subscriptions:
            cat = sub["category"]
            if cat not in by_category:
                by_category[cat] = {"count": 0, "monthly_cost": 0.0}
            by_category[cat]["count"] += 1
            by_category[cat]["monthly_cost"] += sub["avg_monthly_cost"]

        most_expensive = max(subscriptions, key=lambda x: x["avg_monthly_cost"])

        return {
            "total_monthly": round(total_monthly, 2),
            "total_annual": round(total_annual, 2),
            "count": len(subscriptions),
            "by_category": by_category,
            "most_expensive": most_expensive,
        }

    def get_cancellation_candidates(
        self, subscriptions: list[dict], months_inactive: int = 2
    ) -> list[dict]:
        """
        Flag subscriptions whose last payment was more than `months_inactive` months ago
        relative to the latest transaction date in the statement — potential forgotten subs.
        """
        if not subscriptions:
            return []

        statement_end = self.df["Date"].max()
        threshold = statement_end - pd.DateOffset(months=months_inactive)

        candidates = []
        for sub in subscriptions:
            last_dt = pd.to_datetime(sub["last_payment"])
            if last_dt < threshold:
                sub_copy = sub.copy()
                months_ago = (statement_end - last_dt).days / 30
                sub_copy["months_since_last"] = round(months_ago, 1)
                candidates.append(sub_copy)

        return sorted(candidates, key=lambda x: x["months_since_last"], reverse=True)

    def get_all_subscriptions(self) -> list[dict]:
        """Return auto-detected + manually added subscriptions in a unified format."""
        detected = self.detect_subscriptions()
        result = [
            {
                "name": s["name"],
                "monthly_cost": s["avg_monthly_cost"],
                "source": "auto",
                "next_payment": s["next_estimated"],
            }
            for s in detected
        ]
        result.extend(self._manual_subscriptions)
        return result

    def get_total_monthly_cost(self) -> float:
        """Return the total monthly cost across all subscriptions."""
        return round(sum(s["monthly_cost"] for s in self.get_all_subscriptions()), 2)

    def get_total_annual_cost(self) -> float:
        """Return the total annual cost across all subscriptions."""
        return round(self.get_total_monthly_cost() * 12, 2)

    def get_upcoming_payments(self, days: int = 7) -> list[dict]:
        """Return subscriptions with a next_payment date within the next `days` days."""
        today = datetime.today().date()
        upcoming = []
        for sub in self.get_all_subscriptions():
            try:
                next_dt = pd.to_datetime(sub["next_payment"]).date()
                delta = (next_dt - today).days
                if 0 <= delta <= days:
                    upcoming.append({**sub, "days_until": delta})
            except Exception:
                continue
        return sorted(upcoming, key=lambda x: x["days_until"])

    def add_manual_subscription(self, name: str, monthly_cost: float, next_payment: str) -> bool:
        """Add a subscription manually. Returns False if a subscription with that name already exists."""
        if any(s["name"].lower() == name.lower() for s in self._manual_subscriptions):
            return False
        self._manual_subscriptions.append(
            {
                "name": name,
                "monthly_cost": round(monthly_cost, 2),
                "source": "manual",
                "next_payment": next_payment,
            }
        )
        return True

    def remove_manual_subscription(self, name: str) -> bool:
        """Remove a manually-added subscription by name. Returns False if not found."""
        before = len(self._manual_subscriptions)
        self._manual_subscriptions = [
            s for s in self._manual_subscriptions if s["name"].lower() != name.lower()
        ]
        return len(self._manual_subscriptions) < before

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _group_similar_transactions(self) -> dict[str, pd.DataFrame]:
        """
        Group expense rows by the first matching known-subscription keyword,
        then fall back to grouping by the first 12 chars of their normalised description.
        """
        groups: dict[str, list] = {}

        for _, row in self._expenses.iterrows():
            norm = row["_norm"]
            matched_key = None

            for keyword in KNOWN_SUBSCRIPTIONS:
                if keyword in norm:
                    matched_key = keyword
                    break

            if matched_key is None:
                # Fallback – group by first 12 chars (catches e.g. "PRIME VIDEO 123")
                matched_key = f"__fallback__{norm[:12].strip()}"

            if matched_key not in groups:
                groups[matched_key] = []
            groups[matched_key].append(row)

        return {k: pd.DataFrame(v) for k, v in groups.items()}

    def _analyse_group(self, group_key: str, group_df: pd.DataFrame) -> dict | None:
        """
        Given a group of transactions, decide if they represent a subscription.
        Returns None if the pattern does not look recurring.
        """
        if len(group_df) < 2:
            return None

        dates = group_df["Date"].sort_values().reset_index(drop=True)
        intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        avg_interval = float(np.mean(intervals))

        # Must match monthly, quarterly, or annual cadence
        is_monthly = MONTHLY_MIN <= avg_interval <= MONTHLY_MAX
        is_quarterly = QUARTERLY_MIN <= avg_interval <= QUARTERLY_MAX
        is_annual = ANNUAL_MIN <= avg_interval <= ANNUAL_MAX

        if not (is_monthly or is_quarterly or is_annual):
            return None

        freq_label = _frequency_label(avg_interval)
        avg_amount = abs(group_df["Amount"].mean())
        monthly_cost = _monthly_equivalent(avg_amount, freq_label)
        annual_cost = round(monthly_cost * 12, 2)

        most_common_desc = group_df["Description"].mode().iloc[0]

        # Resolve display name and category
        is_known = False
        display_name = most_common_desc
        category = "Other"

        if not group_key.startswith("__fallback__"):
            service_info = KNOWN_SUBSCRIPTIONS.get(group_key)
            if service_info:
                display_name, category, _ = service_info
                is_known = True
        else:
            # Try to match against known services by description
            norm = _normalise_description(most_common_desc)
            for keyword, (name, cat, _) in KNOWN_SUBSCRIPTIONS.items():
                if keyword in norm:
                    display_name = name
                    category = cat
                    is_known = True
                    break

        last_payment = dates.iloc[-1]
        first_payment = dates.iloc[0]

        # Estimate next payment
        next_estimated = last_payment + timedelta(days=round(avg_interval))

        return {
            "name": display_name,
            "description": most_common_desc,
            "category": category,
            "known_service": is_known,
            "frequency": freq_label,
            "occurrences": len(group_df),
            "avg_amount": round(avg_amount, 2),
            "avg_monthly_cost": monthly_cost,
            "annual_cost": annual_cost,
            "first_payment": first_payment.strftime("%Y-%m-%d"),
            "last_payment": last_payment.strftime("%Y-%m-%d"),
            "next_estimated": next_estimated.strftime("%Y-%m-%d"),
            "all_amounts": [round(abs(a), 2) for a in group_df["Amount"].tolist()],
        }
