"""Resilience, load, and performance tests for file processing flows."""

from __future__ import annotations

import io
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import pytest

import moneyflow.services.file_processor as file_processor
from moneyflow.parsing.csv_parser import CSVParser


class _SessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self[key] = value


class _FakeStreamlit:
    def __init__(self):
        self.session_state = _SessionState()
        self.errors = []
        self._lock = threading.Lock()

    def error(self, message):
        with self._lock:
            self.errors.append(str(message))


class _FastAnalyzer:
    def __init__(self, df):
        self.df = df

    def get_summary_stats(self):
        return {"rows": len(self.df)}

    def categorize_expenses(self):
        return {"category_totals": {}}

    def identify_recurring_transactions(self):
        return []

    def calculate_monthly_breakdown(self):
        return []

    def generate_budget_recommendations(self):
        return []

    def detect_unusual_transactions(self):
        return []

    def get_top_merchants(self):
        return []


@pytest.fixture
def fake_streamlit(monkeypatch):
    fake = _FakeStreamlit()
    monkeypatch.setattr(file_processor, "st", fake)
    monkeypatch.setattr(file_processor, "FinancialAnalyzer", _FastAnalyzer)
    return fake


class TestFileProcessorErrorHandling:
    def test_process_uploaded_file_returns_false_on_parser_exception(
        self, monkeypatch, fake_streamlit
    ):
        class _ExplodingParser:
            def parse_csv(self, _uploaded_file):
                raise ValueError("Invalid CSV format")

        monkeypatch.setattr(file_processor, "CSVParser", _ExplodingParser)

        ok = file_processor.process_uploaded_file(io.StringIO("bad,data"))

        assert ok is False
        assert fake_streamlit.errors
        assert "Error processing file" in fake_streamlit.errors[-1]

    def test_process_uploaded_file_returns_false_on_empty_dataframe(
        self, monkeypatch, fake_streamlit
    ):
        class _EmptyParser:
            def parse_csv(self, _uploaded_file):
                return pd.DataFrame()

        monkeypatch.setattr(file_processor, "CSVParser", _EmptyParser)

        ok = file_processor.process_uploaded_file(io.StringIO("Date,Description,Amount\n"))

        assert ok is False
        assert any("Could not parse the CSV file" in msg for msg in fake_streamlit.errors)

    def test_process_uploaded_file_populates_financial_data_on_success(
        self, monkeypatch, fake_streamlit
    ):
        class _GoodParser:
            def parse_csv(self, _uploaded_file):
                return pd.DataFrame(
                    {
                        "Date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
                        "Description": ["Salary", "Coffee"],
                        "Amount": [1200.0, -4.5],
                        "Type": ["Income", "Expense"],
                    }
                )

        monkeypatch.setattr(file_processor, "CSVParser", _GoodParser)

        ok = file_processor.process_uploaded_file(io.StringIO("unused"))

        assert ok is True
        assert "financial_data" in fake_streamlit.session_state
        assert set(fake_streamlit.session_state.financial_data.keys()) == {
            "summary",
            "categories",
            "recurring",
            "monthly",
            "recommendations",
            "unusual",
            "top_merchants",
        }


class TestFloodAndLoadBehavior:
    def test_flooded_requests_mixed_valid_and_invalid_are_handled(
        self, monkeypatch, fake_streamlit
    ):
        class _FloodParser:
            def parse_csv(self, uploaded_file):
                text = uploaded_file.getvalue()
                if "MALFORMED" in text:
                    raise ValueError("malformed csv")
                return pd.DataFrame(
                    {
                        "Date": pd.to_datetime(["2026-01-01"]),
                        "Description": ["Request"],
                        "Amount": [1.0],
                        "Type": ["Income"],
                    }
                )

        monkeypatch.setattr(file_processor, "CSVParser", _FloodParser)

        total_requests = 200
        invalid_every = 7

        def _single_call(i):
            payload = (
                "MALFORMED"
                if i % invalid_every == 0
                else "Date,Description,Amount\n2026-01-01,OK,1"
            )
            return file_processor.process_uploaded_file(io.StringIO(payload))

        with ThreadPoolExecutor(max_workers=40) as executor:
            results = list(executor.map(_single_call, range(total_requests)))

        expected_failures = len([i for i in range(total_requests) if i % invalid_every == 0])
        actual_failures = results.count(False)
        actual_success = results.count(True)

        assert actual_failures == expected_failures
        assert actual_success == total_requests - expected_failures

    def test_csv_parsing_large_file_performance_budget(self):
        """
        Benchmark-style test: parse a large CSV and enforce a throughput budget.
        Threshold is intentionally opinionated to catch regressions early.
        """
        row_count = 50_000
        df = pd.DataFrame(
            {
                "Date": pd.date_range("2026-01-01", periods=row_count, freq="min"),
                "Description": ["Load Test Transaction"] * row_count,
                "Amount": np.where(np.arange(row_count) % 3 == 0, 1250.0, -19.99),
                "Balance": np.linspace(10_000, 8_000, row_count),
            }
        )
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        parser = CSVParser()

        start = time.perf_counter()
        parsed = parser.parse_csv(csv_buffer)
        elapsed = time.perf_counter() - start

        rows_per_sec = len(parsed) / elapsed if elapsed > 0 else float("inf")

        assert len(parsed) == row_count
        assert elapsed < 3.0, f"Parsing took {elapsed:.2f}s for {row_count} rows"
        assert rows_per_sec > 15_000, f"Throughput too low: {rows_per_sec:.0f} rows/sec"

    def test_request_flood_end_to_end_latency_budget(self, monkeypatch, fake_streamlit):
        class _FastParser:
            def parse_csv(self, _uploaded_file):
                return pd.DataFrame(
                    {
                        "Date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
                        "Description": ["Salary", "Snack"],
                        "Amount": [100.0, -3.0],
                        "Type": ["Income", "Expense"],
                    }
                )

        monkeypatch.setattr(file_processor, "CSVParser", _FastParser)

        request_count = 300

        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=60) as executor:
            results = list(
                executor.map(
                    lambda _: file_processor.process_uploaded_file(io.StringIO("irrelevant")),
                    range(request_count),
                )
            )
        elapsed = time.perf_counter() - start

        avg_latency_ms = (elapsed / request_count) * 1000

        assert all(results)
        assert avg_latency_ms < 20, f"Average latency too high: {avg_latency_ms:.2f} ms/request"
