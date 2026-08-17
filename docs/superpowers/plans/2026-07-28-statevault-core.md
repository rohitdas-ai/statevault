# StateVault Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and test `statevault-core`, a resilient multi-region memory-as-a-service system unifying ACID transactional state (JSONB) and 1024-dimensional semantic memory (pgvector HNSW) natively in CockroachDB with AWS Lambda handlers and a dark glassmorphic landing page.

**Architecture:** AWS Lambda Sync API receives agent state + memory text, computes 1024d embeddings via Amazon Bedrock Titan Text Embeddings V2, and performs atomic upserts into CockroachDB (`agent_sessions`, `agent_transactional_state`, `agent_semantic_memory`). Asynchronous billing records are queued via Amazon SQS to a background Lambda billing worker charging Paddle Billing.

**Tech Stack:** Python 3.11 (`psycopg2-binary`, `boto3`, `requests`), PostgreSQL / CockroachDB (pgvector, HNSW index), AWS SAM (Lambda, SQS), Vanilla HTML5/CSS3 (Outfit, Inter, Fira Code).

## Global Constraints
- Target Production Domain: `statevault.github.io`
- License: MIT (`LICENSE`)
- Bedrock Embedding Model: `amazon.titan-embed-text-v2:0` (1024 dimensions, normalized)
- Database Indexing: HNSW cosine proximity index (`vector_cosine_ops`, operator `<=>`)
- SQL Type Casting: Vector embeddings MUST be explicitly cast as string literals `"[v1,v2,...]::VECTOR"` to avoid psycopg2 array serialization errors.

---

### Task 1: Project Scaffolding & Environment Setup

**Files:**
- Create: `LICENSE`
- Create: `README.md`
- Create: `env.local`
- Create: `scripts/ccloud_check.sh`

**Interfaces:**
- Consumes: Environment variables (`COCKROACH_DB_URL`, `AWS_REGION`, `TARGET_PRODUCTION_DOMAIN`)
- Produces: Base repository structure and automated ccloud cluster health check utility.

- [ ] **Step 1: Create MIT LICENSE file**

Create `LICENSE`:
```text
MIT License

Copyright (c) 2026 StateVault Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Create environment configuration template `env.local`**

Create `env.local`:
```bash
# CockroachDB Connection URI
COCKROACH_DB_URL="postgresql://your_sql_user:your_sql_password@statevault-db.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full"

# Billing API Keys
PADDLE_API_KEY="paddlesb_api_your_sandbox_bearer_token_string"
PADDLE_PRODUCT_PRICE_ID="pri_your_paddle_product_price_identifier"

# AWS Deployment Identifiers
AWS_ACCOUNT_ID="your_aws_account_number_here"
AWS_REGION="us-east-1"

# Domain Configuration
TARGET_PRODUCTION_DOMAIN="statevault.github.io"
```

- [ ] **Step 3: Create ccloud health check script `scripts/ccloud_check.sh`**

Create `scripts/ccloud_check.sh`:
```bash
#!/bin/bash
# ccloud CLI cluster health check utility
set -euo pipefail

if [ -z "${COCKROACH_API_KEY:-}" ]; then
  echo "Error: COCKROACH_API_KEY environment variable is not set." >&2
  exit 1
fi

echo "Authenticating ccloud CLI..."
ccloud auth login --token "$COCKROACH_API_KEY"

echo "Retrieving cluster configurations in JSON format..."
ccloud cluster list -o json > clusters.json

CLUSTER_NAME="statevault-db"
echo "Validating connectivity status for: $CLUSTER_NAME"
ccloud cluster describe "$CLUSTER_NAME" -o json > cluster_health.json

echo "Infrastructure verification completed successfully."
```

- [ ] **Step 4: Create README documentation `README.md`**

Create `README.md`:
```markdown
# StateVault

Resilient, Multi-Region Memory-as-a-Service for Autonomous AI Agent Networks built on CockroachDB & AWS.

## Architecture
StateVault unifies ACID transactional state (`JSONB`) and high-dimensional semantic memory (`pgvector`) into a single atomic CockroachDB transaction block.

## Quickstart
1. Copy `env.local` to `.env` and fill in credentials.
2. Run database migration: `psql $COCKROACH_DB_URL -f database/schema.sql`
3. Execute agent test harness: `python agent/atlas_agent.py`
4. Deploy serverless stack: `sam build && sam deploy --guided`
```

- [ ] **Step 5: Make script executable & commit**

Run: `chmod +x scripts/ccloud_check.sh`

```bash
git add LICENSE env.local scripts/ccloud_check.sh README.md
git commit -m "feat: add repository scaffolding, license, env config, and ccloud health script"
```

---

### Task 2: CockroachDB Schema & Vector Indexing

**Files:**
- Create: `database/schema.sql`
- Create: `tests/test_schema.py`

**Interfaces:**
- Consumes: CockroachDB SQL connection (`COCKROACH_DB_URL`)
- Produces: SQL DDL defining `developer_accounts`, `agent_sessions`, `agent_transactional_state`, `agent_semantic_memory`, and HNSW index.

- [ ] **Step 1: Write schema unit test `tests/test_schema.py`**

Create `tests/test_schema.py`:
```python
import os
import pytest

def test_schema_sql_exists_and_contains_vector_hnsw():
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    assert os.path.exists(schema_path), "schema.sql missing"
    
    with open(schema_path, "r") as f:
        sql = f.read()
        
    assert "CREATE EXTENSION IF NOT EXISTS vector;" in sql
    assert "CREATE TABLE developer_accounts" in sql
    assert "CREATE TABLE agent_sessions" in sql
    assert "CREATE TABLE agent_transactional_state" in sql
    assert "CREATE TABLE agent_semantic_memory" in sql
    assert "VECTOR(1024)" in sql
    assert "USING hnsw (embedding vector_cosine_ops)" in sql
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_schema.py -v`
Expected: FAIL with `schema.sql missing`

- [ ] **Step 3: Create `database/schema.sql`**

Create `database/schema.sql`:
```sql
-- Enable pgvector support in the database cluster
CREATE EXTENSION IF NOT EXISTS vector;

-- Tenant Developer Accounts
CREATE TABLE developer_accounts (
    developer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paddle_customer_id VARCHAR(255) UNIQUE,
    api_key_hash VARCHAR(64) UNIQUE NOT NULL,
    plan_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Session Context
CREATE TABLE agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    developer_id UUID REFERENCES developer_accounts(developer_id) ON DELETE CASCADE,
    agent_external_id VARCHAR(255) NOT NULL,
    session_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(developer_id, agent_external_id)
);

-- Transactional Memory: Structured operational variables (ACID compliant)
CREATE TABLE agent_transactional_state (
    session_id UUID REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    state_key VARCHAR(255) NOT NULL,
    state_value JSONB NOT NULL,
    version_id INT DEFAULT 1,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (session_id, state_key)
);

-- Semantic Memory: High-dimensional search context (pgvector)
CREATE TABLE agent_semantic_memory (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    raw_content TEXT NOT NULL,
    embedding VECTOR(1024), -- Matched to 1024-dimensions generated by Amazon Titan Embeddings V2
    token_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HNSW Cosine Proximity Index for fast, distributed semantic searches
CREATE INDEX IF NOT EXISTS semantic_memory_hnsw_idx 
ON agent_semantic_memory USING hnsw (embedding vector_cosine_ops);
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest tests/test_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add database/schema.sql tests/test_schema.py
git commit -m "feat: add CockroachDB pgvector HNSW schema and validation test"
```

---

### Task 3: Backend Requirements & AWS Lambda Sync Handler

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/lambda_function.py`
- Create: `tests/test_lambda_function.py`

**Interfaces:**
- Consumes: AWS API Gateway payload (`x-api-key`, `agent_id`, `state_key`, `state_value`, `raw_text_memory`)
- Produces: Atomic write handler in CockroachDB + asynchronous SQS billing message.

- [ ] **Step 1: Create `backend/requirements.txt`**

Create `backend/requirements.txt`:
```text
psycopg2-binary==2.9.9
boto3==1.34.0
requests==2.31.0
pytest==8.0.0
```

- [ ] **Step 2: Write unit test for Lambda Handler logic `tests/test_lambda_function.py`**

Create `tests/test_lambda_function.py`:
```python
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
```

- [ ] **Step 3: Run test to verify failure**

Run: `pytest tests/test_lambda_function.py -v`
Expected: FAIL (lambda_function missing or functions not declared)

- [ ] **Step 4: Create `backend/lambda_function.py`**

Create `backend/lambda_function.py`:
```python
import os
import json
import hashlib
import psycopg2
import boto3
from psycopg2.extras import RealDictCursor

db_url = os.environ.get("COCKROACH_DB_URL", "postgresql://user:pass@localhost:26257/defaultdb")
conn = None

def get_db_connection():
    global conn
    try:
        if conn is None or conn.closed:
            conn = psycopg2.connect(db_url, application_name="statevault_dual_sync_engine")
        else:
            with conn.cursor() as test_cur:
                test_cur.execute("SELECT 1")
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        conn = psycopg2.connect(db_url, application_name="statevault_dual_sync_engine")
    return conn

current_region = os.environ.get("AWS_REGION", "us-east-1")
bedrock_client = boto3.client(service_name="bedrock-runtime", region_name=current_region)
sqs_client = boto3.client(service_name="sqs", region_name=current_region)

aws_account = os.environ.get("AWS_ACCOUNT_ID", "000000000000")
billing_queue_url = f"https://sqs.{current_region}.amazonaws.com/{aws_account}/statevault-billing-queue-{current_region}"

def generate_embedding_coordinates(text_content):
    payload = json.dumps({
        "inputText": text_content,
        "dimensions": 1024,
        "normalize": True
    })
    
    response = bedrock_client.invoke_model(
        body=payload,
        modelId="amazon.titan-embed-text-v2:0",
        accept="application/json",
        contentType="application/json"
    )
    
    response_body = json.loads(response["body"].read().decode("utf-8"))
    return response_body["embedding"]

def handler(event, context):
    try:
        connection = get_db_connection()
        
        api_key = event.get("headers", {}).get("x-api-key")
        if not api_key:
            return {
                "statusCode": 401,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Unauthorized. Missing API Authorization Header."})
            }
        
        api_key_hash = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
        payload = json.loads(event.get("body", "{}"))
        
        agent_external_id = payload["agent_id"]
        state_key = payload["state_key"]
        state_value = payload["state_value"]
        raw_text_memory = payload["raw_text_memory"]
        
        vector_embedding = generate_embedding_coordinates(raw_text_memory)
        
        with connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT developer_id, paddle_customer_id, plan_tier FROM developer_accounts WHERE api_key_hash = %s", (api_key_hash,))
            dev_record = cur.fetchone()
            if not dev_record:
                return {
                    "statusCode": 403,
                    "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                    "body": json.dumps({"error": "Forbidden. Developer Tenant Verification Failed."})
                }
            
            dev_id = dev_record["developer_id"]
            paddle_cust_id = dev_record["paddle_customer_id"]
            plan_tier = dev_record["plan_tier"]
            
            cur.execute('''
                INSERT INTO agent_sessions (developer_id, agent_external_id, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (developer_id, agent_external_id) 
                DO UPDATE SET updated_at = NOW() RETURNING session_id;
            ''', (dev_id, agent_external_id))
            session_id = cur.fetchone()["session_id"]
            
            cur.execute('''
                INSERT INTO agent_transactional_state (session_id, state_key, state_value, version_id, updated_at)
                VALUES (%s, %s, %s::JSONB, 1, NOW())
                ON CONFLICT (session_id, state_key)
                DO UPDATE SET state_value = EXCLUDED.state_value, version_id = agent_transactional_state.version_id + 1, updated_at = NOW();
            ''', (session_id, state_key, json.dumps(state_value)))
            
            cur.execute('''
                INSERT INTO agent_semantic_memory (session_id, raw_content, embedding)
                VALUES (%s, %s, %s::VECTOR);
            ''', (session_id, raw_text_memory, str(vector_embedding)))
            
            connection.commit()
            
        if plan_tier != "free" and paddle_cust_id:
            try:
                sqs_client.send_message(
                    QueueUrl=billing_queue_url,
                    MessageBody=json.dumps({"paddle_customer_id": paddle_cust_id, "units": 1})
                )
            except Exception as sqs_err:
                print(f"Warning: Failed to enqueue billing record: {sqs_err}")
            
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"status": "success", "session_id": str(session_id), "synchronized": True})
        }
        
    except Exception as e:
        if 'connection' in locals() and connection and not connection.closed:
            connection.rollback()
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)})
        }
```

- [ ] **Step 5: Run test to verify pass**

Run: `pytest tests/test_lambda_function.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/lambda_function.py tests/test_lambda_function.py
git commit -m "feat: add connection-pooled AWS Lambda sync handler and unit tests"
```

---

### Task 4: Semantic Context Recall Engine

**Files:**
- Create: `backend/context_recall.py`
- Create: `tests/test_context_recall.py`

**Interfaces:**
- Consumes: `session_id`, `search_query_string`, `match_limit`
- Produces: Context retrieval dictionary containing operational states and HNSW vector distance matches (`ORDER BY embedding <=> %s::VECTOR ASC`).

- [ ] **Step 1: Write unit test for context recall `tests/test_context_recall.py`**

Create `tests/test_context_recall.py`:
```python
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
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_context_recall.py -v`
Expected: FAIL (context_recall missing)

- [ ] **Step 3: Create `backend/context_recall.py`**

Create `backend/context_recall.py`:
```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from lambda_function import generate_embedding_coordinates

db_url = os.environ.get("COCKROACH_DB_URL", "postgresql://user:pass@localhost:26257/defaultdb")

def execute_semantic_context_retrieval(session_id, search_query_string, match_limit=5):
    """
    Retrieves both the active transactional state variables and relevant semantic
    memories (using Cosine Distance search) for an agent session.
    """
    query_vector_coordinates = generate_embedding_coordinates(search_query_string)
    
    read_conn = psycopg2.connect(db_url, application_name="statevault_read_engine")
    try:
        with read_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT state_key, state_value FROM agent_transactional_state WHERE session_id = %s", (session_id,))
            active_operational_states = cur.fetchall()
            
            cur.execute('''
                SELECT raw_content, created_at, (embedding <=> %s::VECTOR) as spatial_distance_score 
                FROM agent_semantic_memory 
                WHERE session_id = %s
                ORDER BY embedding <=> %s::VECTOR ASC 
                LIMIT %s;
            ''', (str(query_vector_coordinates), session_id, str(query_vector_coordinates), match_limit))
            semantic_historical_matches = cur.fetchall()
            
        return {
            "transactional_state_context": {row["state_key"]: row["state_value"] for row in active_operational_states},
            "semantic_memory_history": semantic_historical_matches
        }
    finally:
        read_conn.close()
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest tests/test_context_recall.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/context_recall.py tests/test_context_recall.py
git commit -m "feat: add semantic context recall module using pgvector HNSW distance"
```

---

### Task 5: Async Billing Worker & AWS SAM IaC Template

**Files:**
- Create: `backend/billing_worker.py`
- Create: `template.yaml`
- Create: `tests/test_billing_worker.py`

**Interfaces:**
- Consumes: SQS batch event containing `{ "Records": [ { "body": "{\"paddle_customer_id\": \"...\", \"units\": 1}" } ] }`
- Produces: Aggregated Paddle transaction API calls + AWS SAM IaC configuration for CloudFront, Route53, Lambda, and SQS.

- [ ] **Step 1: Write test for Billing Worker `tests/test_billing_worker.py`**

Create `tests/test_billing_worker.py`:
```python
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
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_billing_worker.py -v`
Expected: FAIL (billing_worker missing)

- [ ] **Step 3: Create `backend/billing_worker.py`**

Create `backend/billing_worker.py`:
```python
import os
import json
import requests

def handler(event, context):
    paddle_api_key = os.environ.get("PADDLE_API_KEY", "")
    price_id = os.environ.get("PADDLE_PRODUCT_PRICE_ID", "")
    
    aggregated_usage = {}
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        cust_id = body["paddle_customer_id"]
        units = body["units"]
        aggregated_usage[cust_id] = aggregated_usage.get(cust_id, 0) + units
        
    failed_customers = []
    
    for customer_id, total_units in aggregated_usage.items():
        url = "https://sandbox-api.paddle.com/transactions"
        headers = {
            "Authorization": f"Bearer {paddle_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "status": "billed",
            "collection_mode": "manual",
            "customer_id": customer_id,
            "items": [{"price_id": price_id, "quantity": total_units}]
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=5)
            response.raise_for_status()
        except Exception as e:
            print(f"Paddle Sync Error for customer {customer_id}: {str(e)}")
            failed_customers.append(customer_id)
            
    if failed_customers:
        print(f"Warning: Failed to bill the following customers in batch: {failed_customers}")
        
    return {
        "status": "partial_success" if failed_customers else "success",
        "processed_clients": len(aggregated_usage) - len(failed_customers)
    }
```

- [ ] **Step 4: Create AWS SAM infrastructure template `template.yaml`**

Create `template.yaml`:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: StateVault Resilient Multi-Region Memory Engine Infrastructure

Globals:
  Function:
    Timeout: 15
    Runtime: python3.11
    MemorySize: 256
    Environment:
      Variables:
        COCKROACH_DB_URL: !Ref CockroachDbUrl
        PADDLE_API_KEY: !Ref PaddleApiKey
        PADDLE_PRODUCT_PRICE_ID: !Ref PaddlePriceId

Parameters:
  CockroachDbUrl:
    Type: String
    NoEcho: true
  PaddleApiKey:
    Type: String
    NoEcho: true
  PaddlePriceId:
    Type: String

Resources:
  BillingQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub "statevault-billing-queue-${AWS::Region}"

  StateVaultSyncApi:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: backend/
      Handler: lambda_function.handler
      Events:
        SyncApiEvent:
          Type: Api
          Properties:
            Path: /v1/sync
            Method: post

  BillingWorkerFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: backend/
      Handler: billing_worker.handler
      Events:
        SQSEvent:
          Type: SQS
          Properties:
            Queue: !GetAtt BillingQueue.Arn
            BatchSize: 10
```

- [ ] **Step 5: Run tests to verify pass**

Run: `pytest tests/test_billing_worker.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/billing_worker.py template.yaml tests/test_billing_worker.py
git commit -m "feat: add SQS billing worker and AWS SAM infrastructure template"
```

---

### Task 6: Atlas Agent Application Test Harness

**Files:**
- Create: `agent/atlas_agent.py`
- Create: `tests/test_atlas_agent.py`

**Interfaces:**
- Consumes: StateVault API endpoint URL + API Key
- Produces: Multi-turn agent execution simulator validating persistent memory writes across state turns.

- [ ] **Step 1: Write test for Atlas Agent `tests/test_atlas_agent.py`**

Create `tests/test_atlas_agent.py`:
```python
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
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_atlas_agent.py -v`
Expected: FAIL (atlas_agent missing)

- [ ] **Step 3: Create `agent/atlas_agent.py`**

Create `agent/atlas_agent.py`:
```python
import os
import requests

STATEVAULT_API = os.environ.get("STATEVAULT_API_URL", "https://api.statevault.site/v1/sync")
API_KEY = os.environ.get("STATEVAULT_API_KEY", "statevault_test_token_secret_abc")

class AtlasAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.state = {"step": 0, "status": "initialized", "tasks_completed": []}

    def execute_task(self, task_name, memory_text):
        print(f"[{self.agent_id}] Executing task: {task_name}")
        self.state["step"] += 1
        self.state["tasks_completed"].append(task_name)
        self.state["status"] = "processing"
        
        self._sync_memory(memory_text)
        
    def _sync_memory(self, text):
        payload = {
            "agent_id": self.agent_id,
            "state_key": "active_workflow_state",
            "state_value": self.state,
            "raw_text_memory": text
        }
        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        
        try:
            response = requests.post(STATEVAULT_API, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"[{self.agent_id}] Memory synced to CockroachDB successfully.")
            else:
                print(f"[{self.agent_id}] Response: {response.text}")
        except Exception as e:
            print(f"[{self.agent_id}] Network Exception: {str(e)}")

if __name__ == "__main__":
    agent = AtlasAgent("atlas_prod_01")
    agent.execute_task("analyze_logs", "Found anomalous login spikes in us-east-1.")
    agent.execute_task("block_ip", "Blocked IP range 192.168.1.0/24 due to suspicious activity.")
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest tests/test_atlas_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/atlas_agent.py tests/test_atlas_agent.py
git commit -m "feat: add Atlas Agent application test harness"
```

---

### Task 7: Landing Page & Documentation Dashboard

**Files:**
- Create: `public/index.html`
- Create: `tests/test_landing_page.py`

**Interfaces:**
- Consumes: Web browsers requesting `statevault.github.io`
- Produces: Dark glassmorphic landing page with Outfit/Inter typography, interactive code copy widget, and metered pricing grid.

- [ ] **Step 1: Write test for landing page `tests/test_landing_page.py`**

Create `tests/test_landing_page.py`:
```python
import os
import pytest

def test_landing_page_html_structure():
    html_path = os.path.join(os.path.dirname(__file__), "..", "public", "index.html")
    assert os.path.exists(html_path), "index.html missing"
    
    with open(html_path, "r") as f:
        html = f.read()
        
    assert "<!DOCTYPE html>" in html
    assert "StateVault" in html
    assert "CockroachDB" in html
    assert "copy-btn" in html
    assert "pricing-card" in html
    assert "https://fonts.googleapis.com/css2?family=Inter" in html
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_landing_page.py -v`
Expected: FAIL (index.html missing)

- [ ] **Step 3: Create `public/index.html`**

Create `public/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="StateVault - Persistent, multi-region memory-as-a-service for AI agent networks. Unify transactional state and vector memories natively in CockroachDB.">
  <title>StateVault | Memory-as-a-Service for AI Agents</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Inter:wght@400;500;600&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
  
  <style>
    :root {
      --bg-dark: #090616;
      --card-bg: rgba(22, 17, 45, 0.6);
      --card-hover: rgba(29, 23, 60, 0.85);
      --border-color: rgba(139, 92, 246, 0.2);
      --border-hover: rgba(139, 92, 246, 0.55);
      --accent-purple: #8b5cf6;
      --accent-cyan: #06b6d4;
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --font-family: 'Inter', sans-serif;
      --font-display: 'Outfit', sans-serif;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg-dark);
      background-image: 
        radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.15) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(6, 182, 212, 0.1) 0%, transparent 45%);
      color: var(--text-primary);
      font-family: var(--font-family);
      line-height: 1.6;
      min-height: 100vh;
      padding: 40px 20px;
    }

    header {
      max-width: 1000px;
      margin: 0 auto 50px auto;
      text-align: center;
    }

    .badge {
      display: inline-block;
      padding: 6px 16px;
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%);
      border: 1px solid var(--border-color);
      border-radius: 100px;
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--accent-cyan);
      margin-bottom: 20px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    h1 {
      font-family: var(--font-display);
      font-size: 3rem;
      font-weight: 800;
      line-height: 1.1;
      margin-bottom: 20px;
      background: linear-gradient(135deg, #ffffff 30%, #a78bfa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .lead {
      font-size: 1.2rem;
      color: var(--text-secondary);
      max-width: 700px;
      margin: 0 auto;
    }

    main {
      max-width: 1000px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 1fr;
      gap: 40px;
    }

    .card {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 30px;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
    }

    .card:hover {
      transform: translateY(-4px);
      border-color: var(--border-hover);
      box-shadow: 0 12px 30px rgba(139, 92, 246, 0.15);
    }

    h2 {
      font-family: var(--font-display);
      font-size: 1.75rem;
      margin-bottom: 20px;
    }

    .snippet-container {
      position: relative;
      background-color: rgba(9, 6, 22, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      padding: 20px;
      margin-top: 15px;
      overflow-x: auto;
    }

    pre {
      font-family: 'Fira Code', monospace;
      font-size: 0.9rem;
      color: #e2e8f0;
    }

    .copy-btn {
      position: absolute;
      top: 12px;
      right: 12px;
      background: var(--border-color);
      border: 1px solid var(--border-color);
      color: var(--text-primary);
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.8rem;
    }

    .copy-btn:hover {
      background: var(--accent-purple);
    }

    .pricing-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 24px;
    }

    @media (min-width: 768px) {
      .pricing-grid { grid-template-columns: 1fr 1fr; }
    }

    .pricing-card {
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px;
      background: rgba(255, 255, 255, 0.02);
    }

    .pricing-card.premium {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(6, 182, 212, 0.03) 100%);
      border-color: rgba(139, 92, 246, 0.4);
    }
  </style>
</head>
<body>

  <header>
    <div class="badge">CockroachDB × AWS Hackathon</div>
    <h1>StateVault Memory System</h1>
    <p class="lead">Resilient, multi-region memory-as-a-service for AI agent networks unifying ACID transactional state and pgvector semantic search.</p>
  </header>

  <main>
    <section class="card">
      <h2>Quickstart Integration</h2>
      <p>Sync operational state and raw text memory atomically in a single HTTP POST request:</p>
      
      <div class="snippet-container">
        <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('code-snippet').innerText)">Copy</button>
        <pre id="code-snippet"><code>import requests

payload = {
    "agent_id": "atlas_prod_01",
    "state_key": "active_workflow_state",
    "state_value": {"step": 1, "status": "processing"},
    "raw_text_memory": "Anomalous traffic detected from region us-east-1."
}
headers = {"x-api-key": "YOUR_STATEVAULT_API_KEY"}

response = requests.post("https://api.statevault.site/v1/sync", json=payload, headers=headers)
print(response.json())</code></pre>
      </div>
    </section>

    <section class="card">
      <h2>Metered Pricing Tiers</h2>
      <div class="pricing-grid">
        <div class="pricing-card">
          <h3>Developer Free</h3>
          <p>Ideal for prototyping and single-agent testing.</p>
          <ul style="list-style:none; margin: 15px 0;">
            <li>✓ 10,000 Atomic Syncs / month</li>
            <li>✓ 1024d Titan Vector Indexing</li>
            <li>✓ CockroachDB Serverless Storage</li>
          </ul>
        </div>
        <div class="pricing-card premium">
          <h3>Agentic Pro</h3>
          <p>Metered usage for production multi-agent swarms.</p>
          <ul style="list-style:none; margin: 15px 0;">
            <li>✓ Unlimited Atomic Syncs ($0.001 / req)</li>
            <li>✓ Active-Active Multi-Region (us-east-1 / us-west-2)</li>
            <li>✓ SQS Paddle Automated Billing</li>
          </ul>
        </div>
      </div>
    </section>
  </main>

</body>
</html>
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest tests/test_landing_page.py -v`
Expected: PASS

- [ ] **Step 5: Run all test suites**

Run: `pytest -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add public/index.html tests/test_landing_page.py
git commit -m "feat: add dark glassmorphism landing page and comprehensive test suite"
```
