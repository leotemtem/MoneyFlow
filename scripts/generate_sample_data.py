# SPDX-License-Identifier: MIT
"""Generate a larger synthetic bank statement CSV for demos and manual testing.

The output is fully synthetic (seeded RNG, fictional merchants) and safe to
share. Usage:

    python scripts/generate_sample_data.py --months 6 --out sample_data/generated.csv
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta

MERCHANTS = [
    ("Tesco Supermarket", -1, (25, 95)),
    ("Sainsbury's Grocery", -1, (20, 80)),
    ("Costa Coffee", -1, (3, 6)),
    ("Shell Petrol Station", -1, (40, 70)),
    ("Amazon Purchase", -1, (10, 120)),
    ("Uber Ride", -1, (6, 25)),
    ("Restaurant Bill", -1, (25, 90)),
    ("Pharmacy", -1, (5, 40)),
]

RECURRING = [
    ("Netflix Subscription", -15.99, 5),
    ("Spotify Subscription", -11.99, 12),
    ("Gym Membership", -40.00, 1),
    ("Electricity Bill", -88.00, 20),
]


def generate(months: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    start = date.today().replace(day=1) - timedelta(days=months * 31)
    rows: list[dict] = []
    balance = 2500.0

    for m in range(months):
        month_start = (start + timedelta(days=m * 31)).replace(day=1)

        # Monthly salary
        balance += 2600.0
        rows.append(
            {
                "Date": month_start.replace(day=1),
                "Description": "Salary Deposit",
                "Amount": 2600.00,
                "Balance": round(balance, 2),
            }
        )

        # Recurring payments on fixed days
        for desc, amount, day in RECURRING:
            try:
                d = month_start.replace(day=day)
            except ValueError:
                continue
            balance += amount
            rows.append(
                {"Date": d, "Description": desc, "Amount": amount, "Balance": round(balance, 2)}
            )

        # Random day-to-day spending
        for _ in range(rng.randint(12, 20)):
            name, sign, (lo, hi) = rng.choice(MERCHANTS)
            amount = round(sign * rng.uniform(lo, hi), 2)
            d = month_start + timedelta(days=rng.randint(0, 27))
            balance += amount
            rows.append(
                {"Date": d, "Description": name, "Amount": amount, "Balance": round(balance, 2)}
            )

    rows.sort(key=lambda r: r["Date"])
    for r in rows:
        r["Date"] = r["Date"].isoformat()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="sample_data/generated_statement.csv")
    args = parser.parse_args()

    rows = generate(args.months, args.seed)
    with open(args.out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["Date", "Description", "Amount", "Balance"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic transactions to {args.out}")


if __name__ == "__main__":
    main()
