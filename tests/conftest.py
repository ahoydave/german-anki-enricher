import pytest


def pytest_configure(config):
    config.addinivalue_line('markers', 'manual: requires a real ANTHROPIC_API_KEY and makes live API calls')
