# StateVault: Resilient Multi-Region Memory-as-a-Service for AI Agent Networks

**Date:** 2026-07-28  
**Status:** Approved  
**Target Domain:** `statevault.github.io`  
**Target Architecture:** CockroachDB (pgvector + JSONB) × AWS (Bedrock + Lambda + SQS)  

---

## 1. Executive Summary & Purpose

StateVault is a resilient multi-region memory layer designed for autonomous AI agent networks. It solves the "split-brain" problem inherent in modern AI stack architectures—where structured transactional state and high-dimensional semantic vector memory are stored in disparate databases, risking state corruption during partial failures.

By leveraging CockroachDB's dual engine (pgvector HNSW index + ACID JSONB transactional storage), StateVault performs atomic updates of operational state and 1024-dimensional semantic embeddings within a single database transaction.

---

## 2. System Architecture & Repository Layout

### 2.1 Repository Structure
```text
statevault-core/
├── LICENSE                    # Detectable MIT License File
├── README.md                  # Complete Setup & Execution Guide
├── template.yaml              # AWS SAM Infrastructure-as-Code Template
├── env.local                  # Environment Configuration Template
├── database/
│   └── schema.sql             # CockroachDB DDL/DML with pgvector HNSW
├── backend/
│   ├── lambda_function.py     # Connection-pooled sync API handler
│   ├── context_recall.py      # Semantic vector search engine
│   ├── billing_worker.py      # SQS aggregated Paddle billing worker
│   └── requirements.txt       # Dependencies (psycopg2-binary, boto3, requests)
├── agent/
│   └── atlas_agent.py         # Multi-turn test agent application
├── scripts/
│   └── ccloud_check.sh        # ccloud CLI automated health checker
└── public/
    └── index.html             # Glassmorphism landing page & documentation
```

### 2.2 Core Data Flow

```
[Atlas Agent / Client]
         │
         ▼
[AWS Lambda Sync API] (x-api-key Auth)
         │
         ├───► [Amazon Bedrock (Titan Embeddings V2)] ──► 1024d Vector Coordinates
         │
         ├───► [CockroachDB Cluster] (Single Atomic Transaction Block)
         │       ├── Upsert Session Context (`agent_sessions`)
         │       ├── Upsert Operational State (`agent_transactional_state`)
         │       └── Insert Semantic Memory (`agent_semantic_memory`)
         │
         └───► [Amazon SQS Queue] (Non-blocking Async Usage Event)
                     │
                     ▼
             [Lambda Billing Worker] ──► [Paddle Sandbox API]
```

---

## 3. Database Schema Specification (`database/schema.sql`)

```sql
-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Developer Accounts
CREATE TABLE developer_accounts (
    developer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paddle_customer_id VARCHAR(255) UNIQUE,
    api_key_hash VARCHAR(64) UNIQUE NOT NULL,
    plan_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Sessions
CREATE TABLE agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    developer_id UUID REFERENCES developer_accounts(developer_id) ON DELETE CASCADE,
    agent_external_id VARCHAR(255) NOT NULL,
    session_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(developer_id, agent_external_id)
);

-- Transactional Memory (ACID JSONB)
CREATE TABLE agent_transactional_state (
    session_id UUID REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    state_key VARCHAR(255) NOT NULL,
    state_value JSONB NOT NULL,
    version_id INT DEFAULT 1,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (session_id, state_key)
);

-- Semantic Memory (1024-dimensional vectors)
CREATE TABLE agent_semantic_memory (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    raw_content TEXT NOT NULL,
    embedding VECTOR(1024),
    token_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HNSW Cosine Distance Index
CREATE INDEX IF NOT EXISTS semantic_memory_hnsw_idx 
ON agent_semantic_memory USING hnsw (embedding vector_cosine_ops);
```

---

## 4. Backend Service Specifications

### 4.1 Sync API Handler (`backend/lambda_function.py`)
- **Connection Management:** Global `get_db_connection()` pool with `SELECT 1` liveness ping.
- **Embedding Generation:** Bedrock model `amazon.titan-embed-text-v2:0` (1024 dimensions, normalized).
- **Type Casting Safety:** Pass vector embedding parameters as formatted string literals `"[val1, val2, ...]::VECTOR"` to prevent psycopg2 array serialization errors.
- **Billing Event Enqueue:** Push `{ "paddle_customer_id": ..., "units": 1 }` to SQS without raising exceptions on queue timeout.

### 4.2 Context Recall Engine (`backend/context_recall.py`)
- Execute similarity query using HNSW cosine operator (`<=>`).
- SQL clause: `ORDER BY embedding <=> %s::VECTOR ASC LIMIT %s`.

### 4.3 Billing Worker (`backend/billing_worker.py`)
- Parse SQS batch payload, aggregate unit counts per `paddle_customer_id`.
- Call Paddle API `POST https://sandbox-api.paddle.com/transactions`.

---

## 5. Agent Application (`agent/atlas_agent.py`)

- Multi-turn execution simulator demonstrating sequential task execution (`analyze_logs` -> `block_ip`).
- Sends JSON payloads containing current operational state and task trace text to StateVault endpoint.

---

## 6. Landing Page Specifications (`public/index.html`)

- **Design Tokens:** Dark background `#090616`, glassmorphism backdrop blur `12px`, purple glow `#8b5cf6`, cyan accent `#06b6d4`.
- **Typography:** Outfit (headings), Inter (body), Fira Code (code snippets).
- **Interactive Widgets:** Click-to-copy code blocks for Python Quickstart snippet.
- **SEO:** Meta description, open graph tags, descriptive `<h1>`, fully responsive CSS grid layout.

---

## 7. Verification & Success Criteria

1. Schema applies cleanly without syntax errors in CockroachDB console/psycopg2.
2. Vector embeddings match 1024 dimensions.
3. Single transaction block commits state + vector atomically.
4. Landing page renders cleanly in browser.
5. Atlas agent successfully syncs state and memory across multiple turns.
