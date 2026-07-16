# SPDX-License-Identifier: MIT
"""Streamlit entry point.

Run locally with:  streamlit run streamlit_app.py

Requires the package to be importable (``pip install -e .`` or ``pip install .``).
As a fallback for running from a source checkout without installation, the local
``src`` directory is added to ``sys.path``.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from moneyflow.ui.app import main  # noqa: E402

main()
