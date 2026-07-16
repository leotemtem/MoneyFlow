"""
CSV Parser for Bank Statements
Handles various CSV formats and standardizes the data
"""

import pandas as pd


class CSVParser:
    """Parse and standardize bank statement CSV files"""

    def __init__(self):
        self.df = None
        self.date_column = None
        self.description_column = None
        self.amount_column = None
        self.debit_column = None
        self.credit_column = None
        self.balance_column = None

    def detect_columns(self, df):
        """Automatically detect relevant columns in the CSV"""
        columns = df.columns.tolist()

        # Common column name patterns
        date_patterns = ["date", "transaction date", "posted date", "value date"]
        desc_patterns = ["description", "merchant", "details", "transaction", "payee"]
        amount_patterns = ["amount", "value", "transaction amount"]
        debit_patterns = ["debit"]
        credit_patterns = ["credit"]
        balance_patterns = ["balance", "running balance", "account balance"]

        # Detect date column
        for col in columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in date_patterns):
                self.date_column = col
                break

        # Detect description column
        for col in columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in desc_patterns):
                self.description_column = col
                break

        # Detect debit-only and credit-only columns first
        for col in columns:
            col_lower = col.lower()
            if any(pattern == col_lower for pattern in debit_patterns):
                self.debit_column = col
                break
        for col in columns:
            col_lower = col.lower()
            if any(pattern == col_lower for pattern in credit_patterns):
                self.credit_column = col
                break

        # Only use a single amount column if there are no separate debit/credit columns
        if not (self.debit_column and self.credit_column):
            for col in columns:
                col_lower = col.lower()
                if any(
                    pattern in col_lower
                    for pattern in amount_patterns + debit_patterns + credit_patterns
                ):
                    self.amount_column = col
                    break

        # Detect balance column
        for col in columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in balance_patterns):
                self.balance_column = col
                break

        return {
            "date": self.date_column,
            "description": self.description_column,
            "amount": self.amount_column,
            "debit": self.debit_column,
            "credit": self.credit_column,
            "balance": self.balance_column,
        }

    def parse_csv(
        self, file_path_or_buffer, date_col=None, desc_col=None, amount_col=None, balance_col=None
    ):
        """
        Parse CSV file and standardize format

        Args:
            file_path_or_buffer: Path to CSV or file buffer
            date_col: Optional manual date column name
            desc_col: Optional manual description column name
            amount_col: Optional manual amount column name
            balance_col: Optional manual balance column name

        Returns:
            Standardized DataFrame
        """
        # Read CSV
        self.df = pd.read_csv(file_path_or_buffer)

        # Manual column mapping or auto-detect
        if date_col:
            self.date_column = date_col
        if desc_col:
            self.description_column = desc_col
        if amount_col:
            self.amount_column = amount_col
        if balance_col:
            self.balance_column = balance_col

        # Auto-detect if not manually specified
        detected = self.detect_columns(self.df)

        if not self.date_column:
            self.date_column = detected["date"]
        if not self.description_column:
            self.description_column = detected["description"]
        if not self.amount_column:
            self.amount_column = detected["amount"]
        if not self.debit_column:
            self.debit_column = detected["debit"]
        if not self.credit_column:
            self.credit_column = detected["credit"]
        if not self.balance_column:
            self.balance_column = detected["balance"]

        # Validate required columns are present
        has_amount = self.amount_column or (self.debit_column and self.credit_column)
        if not has_amount:
            raise ValueError(
                "Missing required column: could not find an Amount (or Debit/Credit) "
                "column. Please check your CSV format."
            )

        # Standardize DataFrame
        standardized_df = self._standardize_dataframe()

        return standardized_df

    def _standardize_dataframe(self):
        """Create standardized DataFrame with consistent column names"""
        if self.df is None:
            return pd.DataFrame()
        standard_df = pd.DataFrame()

        # Date column
        if self.date_column:
            standard_df["Date"] = pd.to_datetime(self.df[self.date_column], errors="coerce")

        # Description column
        if self.description_column:
            desc = self.df[self.description_column].astype(str)
            # Sanitize formula injection (CSV injection prevention)
            desc = desc.str.replace(r"^([=+\-@])", r"'\1", regex=True)
            standard_df["Description"] = desc

        # Amount column — handle both split Debit/Credit and single Amount columns
        def _clean_numeric(series):
            s = series.astype(str)
            s = s.str.replace("£", "").str.replace("$", "").str.replace(",", "")
            s = s.str.replace("€", "").str.replace("¥", "")
            return pd.to_numeric(s, errors="coerce").fillna(0)

        if self.debit_column and self.credit_column:
            debits = _clean_numeric(self.df[self.debit_column])
            credits = _clean_numeric(self.df[self.credit_column])
            # Credits are positive (income), debits are negative (expenses)
            standard_df["Amount"] = credits - debits
        elif self.amount_column:
            amounts = self.df[self.amount_column].astype(str)
            amounts = amounts.str.replace("£", "").str.replace("$", "").str.replace(",", "")
            amounts = amounts.str.replace("€", "").str.replace("¥", "")
            standard_df["Amount"] = pd.to_numeric(amounts, errors="coerce")

        # Balance column
        if self.balance_column:
            balances = self.df[self.balance_column].astype(str)
            balances = balances.str.replace("£", "").str.replace("$", "").str.replace(",", "")
            balances = balances.str.replace("€", "").str.replace("¥", "")
            standard_df["Balance"] = pd.to_numeric(balances, errors="coerce")

        # Categorize transactions
        standard_df["Type"] = standard_df["Amount"].apply(
            lambda x: "Income" if x > 0 else "Expense" if x < 0 else "Neutral"
        )

        # Remove rows with missing critical data
        standard_df = standard_df.dropna(subset=["Date", "Amount"])

        # Sort by date
        standard_df = standard_df.sort_values("Date").reset_index(drop=True)

        return standard_df

    def get_column_info(self):
        """Return detected column information"""
        return {
            "date_column": self.date_column,
            "description_column": self.description_column,
            "amount_column": self.amount_column,
            "debit_column": self.debit_column,
            "credit_column": self.credit_column,
            "balance_column": self.balance_column,
            "all_columns": self.df.columns.tolist() if self.df is not None else [],
        }
