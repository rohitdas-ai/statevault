import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import context_recall

@patch("psycopg2.connect")
@patch("context_recall.generate_embedding_coordinates")
def test_execute_semantic_context_retrieval(mock_embed, mock_connect):
    mock_embed.return_value = [0.1] * 1024
    
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    mock_cur.fetchall.side_effect = [
        [{"state_key": "step", "state_value": 2}], # Operational states
        [{"raw_content": "Anomalous spike", "created_at": "2026-07-28", "spatial_distance_score": 0.05}] # Semantic matches
    ]
    
    result = context_recall.execute_semantic_context_retrieval("sess-123", "query anomaly", match_limit=3)
    
    assert "transactional_state_context" in result
    assert result["transactional_state_context"]["step"] == 2
    assert len(result["semantic_memory_history"]) == 1
    assert result["semantic_memory_history"][0]["raw_content"] == "Anomalous spike"
