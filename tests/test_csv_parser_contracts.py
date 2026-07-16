"""Contract-style tests for CSV parsing hardening and input sanitization expectations."""

from __future__ import annotations

import io

import pandas as pd
import pytest

from moneyflow.auth.validators import InputValidator
from moneyflow.parsing.csv_parser import CSVParser


class TestCSVParserContracts:
    def test_parse_csv_normalizes_single_amount_format(self):
        parser = CSVParser()
        csv_data = io.StringIO(
            "\n".join(
                [
                    "Date,Description,Amount,Balance",
                    '2026-01-05,Coffee,-4.50,"£995.50"',
                    '2026-01-01,Salary,2500.00,"£1,000.00"',
                ]
            )
        )

        result = parser.parse_csv(csv_data)

        assert list(result.columns) == ["Date", "Description", "Amount", "Balance", "Type"]
        assert len(result) == 2
        assert result.iloc[0]["Date"] == pd.Timestamp("2026-01-01")
        assert result.iloc[0]["Type"] == "Income"
        assert result.iloc[1]["Type"] == "Expense"
        assert float(result.iloc[0]["Balance"]) == pytest.approx(1000.00)

    def test_parse_csv_with_split_debit_credit_columns(self):
        parser = CSVParser()
        csv_data = io.StringIO(
            "\n".join(
                [
                    "Transaction Date,Merchant,Debit,Credit",
                    "2026-02-01,Salary,,2100.00",
                    "2026-02-02,Groceries,65.25,",
                    "2026-02-03,Cashback,0,2.50",
                ]
            )
        )

        result = parser.parse_csv(csv_data)

        assert len(result) == 3
        assert result["Amount"].tolist() == [2100.00, -65.25, 2.50]
        assert result["Type"].tolist() == ["Income", "Expense", "Income"]

    def test_parse_csv_drops_rows_with_invalid_dates_and_amounts(self):
        parser = CSVParser()
        csv_data = io.StringIO(
            "\n".join(
                [
                    "Date,Description,Amount",
                    "2026-03-01,Valid Income,1000",
                    "not-a-date,Invalid Date,42",
                    "2026-03-03,Invalid Amount,not-a-number",
                ]
            )
        )

        result = parser.parse_csv(csv_data)

        assert len(result) == 1
        assert result.iloc[0]["Description"] == "Valid Income"
        assert float(result.iloc[0]["Amount"]) == pytest.approx(1000.0)

    def test_parse_csv_malformed_csv_raises_exception(self):
        parser = CSVParser()
        malformed_csv = io.StringIO('Date,Description,Amount\n2026-01-01,"Broken quote,10.00\n')

        with pytest.raises(Exception):
            parser.parse_csv(malformed_csv)

    def test_parse_csv_rejects_missing_required_columns_with_clear_error(self):
        """
        Security/resilience contract: parser should fail fast with a clear message
        when required financial columns are missing.
        """
        parser = CSVParser()
        csv_data = io.StringIO(
            "\n".join(
                [
                    "Date,Description",
                    "2026-01-01,No amount present",
                ]
            )
        )

        with pytest.raises(ValueError, match="required|missing|amount"):
            parser.parse_csv(csv_data)

    def test_parse_csv_sanitizes_spreadsheet_formula_descriptions(self):
        """
        Security contract: CSV descriptions should be sanitized to avoid spreadsheet
        formula injection on export.
        """
        parser = CSVParser()
        csv_data = io.StringIO(
            "\n".join(
                [
                    "Date,Description,Amount",
                    '2026-01-01,=HYPERLINK("http://evil.example"),-11.50',
                ]
            )
        )

        result = parser.parse_csv(csv_data)
        description = str(result.iloc[0]["Description"]).strip()

        assert not description.startswith(("=", "+", "-", "@"))


class TestInputSanitizationContracts:
    def test_validate_username_accepts_trimmed_whitespace_input(self):
        """
        Sanitization contract: leading/trailing whitespace should be trimmed before
        validation so benign user input is accepted.
        """
        is_valid, _ = InputValidator.validate_username("   john_doe   ")
        assert is_valid

    def test_sanitize_username_produces_valid_identifier(self):
        raw = " 9bad user! name "
        sanitized = InputValidator.sanitize_username(raw)
        is_valid, _ = InputValidator.validate_username(sanitized)

        assert sanitized == "_9bad_user_name_"
        assert is_valid
