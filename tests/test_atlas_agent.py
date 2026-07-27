import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agent")))

import atlas_agent

@patch("requests.post")
def test_atlas_agent_task_execution(mock_post):
    mock_post.return_value.status_code = 200
    
    agent = atlas_agent.AtlasAgent("test_agent_01")
    agent.execute_task("analyze_logs", "High rate of login failures in us-east-1.")
    
    assert agent.state["step"] == 1
    assert "analyze_logs" in agent.state["tasks_completed"]
    assert mock_post.called
    
    payload = mock_post.call_args[1]["json"]
    assert payload["agent_id"] == "test_agent_01"
    assert payload["state_key"] == "active_workflow_state"
    assert payload["raw_text_memory"] == "High rate of login failures in us-east-1."
