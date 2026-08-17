import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.demo_simulation import (
    simulate_split_brain_failure,
    simulate_statevault_dual_sync,
    simulate_multi_region_outage_recovery,
    simulate_context_recall,
    run_all_scenarios
)

def test_split_brain_failure_demonstration():
    result = simulate_split_brain_failure()
    assert result["state_persisted"] is True
    assert result["vector_persisted"] is False
    assert result["memory_corrupted"] is True

def test_statevault_dual_sync_atomic_recovery():
    result = simulate_statevault_dual_sync()
    assert result["atomic_rollback_on_error"] is True
    assert result["retry_success"] is True
    assert result["data_drift"] == 0

def test_multi_region_outage_recovery():
    result = simulate_multi_region_outage_recovery()
    assert result["primary_region"] == "us-east-1"
    assert result["failover_region"] == "us-west-2"
    assert result["reconnected"] is True
    assert result["memory_preserved"] is True

def test_simulate_context_recall():
    result = simulate_context_recall("suspicious network spike")
    assert len(result["memories"]) > 0
    assert "spatial_distance_score" in result["memories"][0]

def test_run_all_scenarios():
    summary = run_all_scenarios(interactive=False)
    assert summary["split_brain"] is True
    assert summary["dual_sync"] is True
    assert summary["outage_recovery"] is True
    assert summary["vector_recall"] is True
