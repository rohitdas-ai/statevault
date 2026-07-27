import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import billing_worker

@patch("requests.post")
def test_billing_worker_aggregates_units_and_posts_to_paddle(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.raise_for_status = MagicMock()
    
    event = {
        "Records": [
            {"body": json.dumps({"paddle_customer_id": "cust_A", "units": 2})},
            {"body": json.dumps({"paddle_customer_id": "cust_A", "units": 3})},
            {"body": json.dumps({"paddle_customer_id": "cust_B", "units": 1})}
        ]
    }
    
    res = billing_worker.handler(event, None)
    assert res["status"] == "success"
    assert res["processed_clients"] == 2
    assert mock_post.call_count == 2
