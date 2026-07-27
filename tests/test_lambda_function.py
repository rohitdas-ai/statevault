import json
import hashlib
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import lambda_function

def test_missing_api_key_returns_401():
    event = {"headers": {}}
    res = lambda_function.handler(event, None)
    assert res["statusCode"] == 401
    body = json.loads(res["body"])
    assert "Unauthorized" in body["error"]

@patch("lambda_function.get_db_connection")
@patch("lambda_function.generate_embedding_coordinates")
def test_valid_request_executes_transaction(mock_embed, mock_db):
    mock_embed.return_value = [0.1] * 1024
    
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    # Mock developer account record
    mock_cur.fetchone.side_effect = [
        {"developer_id": "dev-123", "paddle_customer_id": "cust-123", "plan_tier": "pro"}, # Dev account
        {"session_id": "sess-456"} # Session ID
    ]
    
    raw_key = "test_secret_key"
    key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
    
    event = {
        "headers": {"x-api-key": raw_key},
        "body": json.dumps({
            "agent_id": "agent-007",
            "state_key": "active_step",
            "state_value": {"step": 1},
            "raw_text_memory": "Log anomaly detected"
        })
    }
    
    with patch("lambda_function.sqs_client") as mock_sqs:
        res = lambda_function.handler(event, None)
        assert res["statusCode"] == 200
        body = json.loads(res["body"])
        assert body["status"] == "success"
        assert body["session_id"] == "sess-456"
        assert mock_conn.commit.called
