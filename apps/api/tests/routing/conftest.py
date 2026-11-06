from __future__ import annotations

import pytest
from routing_fakes import FakeCache, FakeLedger


@pytest.fixture
def ledger() -> FakeLedger:
    return FakeLedger()


@pytest.fixture
def cache() -> FakeCache:
    return FakeCache()
