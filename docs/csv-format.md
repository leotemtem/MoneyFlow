# CSV format

MoneyFlow auto-detects columns by name (case-insensitive) and standardises them
to `Date, Description, Amount, Type` (plus `Balance` when present).

## Recognised columns

| Standard field | Detected from (any of) | Required |
| --- | --- | --- |
| Date | `date`, `transaction date`, `posted date`, `value date` | Yes |
| Description | `description`, `merchant`, `details`, `transaction`, `payee` | Recommended |
| Amount | `amount`, `value`, `transaction amount` | Yes* |
| Debit / Credit | `debit` / `credit` | Yes* |
| Balance | `balance`, `running balance`, `account balance` | Optional |

\* Provide **either** a single `Amount` column **or** both `Debit` and `Credit`.

## Sign convention

- Single `Amount` column: **positive = income**, **negative = expense**.
- Split columns: `Credit` = income (positive), `Debit` = expense; MoneyFlow
  computes `Amount = Credit − Debit`.

## Format 1 — single amount column

```csv
Date,Description,Amount,Balance
2024-12-01,Salary Deposit,3500.00,3500.00
2024-12-02,Tesco Supermarket,-85.50,3414.50
2024-12-06,Netflix Subscription,-15.99,3398.51
```

## Format 2 — separate debit/credit columns

```csv
Date,Description,Debit,Credit,Balance
2024-11-01,Salary Deposit,,2600.00,2600.00
2024-11-02,Tesco Supermarket,74.20,,2525.80
2024-11-03,Netflix Subscription,15.99,,2509.81
```

## Handling and safety

- Currency symbols (`£ $ € ¥`) and thousands separators are stripped from
  numeric fields.
- Rows with an unparseable date or amount are dropped.
- Descriptions beginning with `= + - @` are prefixed with `'` to prevent CSV/
  spreadsheet formula injection.
- Rows are sorted by date after parsing.

See working examples in [`../sample_data/`](../sample_data/).
