"""Tests for the in-tree subprocess isolation plugin.

These run *under* the plugin itself (each one in its own spawned subprocess)
so they're a self-validating sanity check.
"""

from __future__ import annotations

import os
import sys

import pytest


def test_each_test_runs_in_its_own_pid(tmp_path):
    """Two tests should observe different PIDs — proof of process isolation.

    Writes our PID to a shared file. If two tests share a process, we'd see
    the same PID written twice. We can't easily test cross-test in one
    method, so we verify that the running PID isn't the parent pytest PID.
    """
    parent_pid_env = os.environ.get("PYTEST_PARENT_PID")
    if parent_pid_env is None:
        pytest.skip("PYTEST_PARENT_PID not set — plugin not active for this run")
    assert os.getpid() != int(parent_pid_env), (
        "test ran in the parent pytest process; isolation plugin inactive"
    )


def test_child_sentinel_is_set():
    """The child-process sentinel envvar must be present in the test."""
    assert os.environ.get("HERMES_ISOLATE_CHILD") == "1", (
        "HERMES_ISOLATE_CHILD should be '1' inside an isolated test"
    )


def test_module_level_state_is_fresh_per_test_part_a():
    """First half of a state-leakage check: set a module-level value."""
    import tests._isolate_state_probe as probe  # noqa: PLC0415

    probe.LEAKED.append("part_a")
    assert probe.LEAKED == ["part_a"]


def test_module_level_state_is_fresh_per_test_part_b():
    """Second half: if state leaked from part_a, this will see ['part_a'].

    Process isolation means the import in part_b reads a fresh module
    with an empty LEAKED list.
    """
    import tests._isolate_state_probe as probe  # noqa: PLC0415

    assert probe.LEAKED == [], (
        f"module-level state leaked across tests: LEAKED={probe.LEAKED!r}"
    )


def test_no_isolate_falls_through(pytestconfig):
    """When --no-isolate is set, sentinel envvar should be absent.

    This test only runs meaningfully when invoked with --no-isolate; with
    isolation active, we expect the sentinel to be set.
    """
    if pytestconfig.getoption("no_isolate", False):
        assert os.environ.get("HERMES_ISOLATE_CHILD") != "1"
    else:
        assert os.environ.get("HERMES_ISOLATE_CHILD") == "1"
