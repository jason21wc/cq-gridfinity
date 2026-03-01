"""Shared pytest configuration and fixtures for gridfinity test suite.

Policy: tests that check isValid() or topology (face/edge counts) MUST use
default fillets. Only tests that check bounding-box dimensions or filenames
may use fillet_interior=False. See WI-2 guardrails in the optimization plan.
"""
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: full-fillet tests (run with -m slow)")
