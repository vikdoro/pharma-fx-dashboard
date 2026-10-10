"""Baseline test so the suite is green from the start of the project."""

import api


def test_package_exposes_version() -> None:
    assert api.__version__ == "0.1.0"
