# Sample data

All files in this directory are **entirely synthetic** and contain no real
people, accounts, or transactions. They exist to demonstrate the supported CSV
formats and to let you try MoneyFlow without uploading your own statement.

| File | Format |
| --- | --- |
| `sample_statement.csv` | Single `Amount` column (positive = income, negative = expense) |
| `sample_statement_debit_credit.csv` | Separate `Debit` and `Credit` columns |

Never place real bank statements in this directory — they would be at risk of
being committed. Your own data belongs in the git-ignored `data/`, `uploads/`,
or a location outside the repository. See [`../scripts/generate_sample_data.py`](../scripts/generate_sample_data.py)
to generate a larger synthetic statement.
