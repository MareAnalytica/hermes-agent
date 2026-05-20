"""Module-level state used by tests/test_isolate_plugin.py.

Two tests both append to ``LEAKED`` and assert its contents — if process
isolation is working, each test's import sees a fresh empty list.
"""

LEAKED: list[str] = []
