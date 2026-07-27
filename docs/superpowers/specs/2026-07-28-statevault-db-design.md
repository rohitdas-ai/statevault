# StateVault Database Design Spec

## 1. Architecture
- **Engine**: CockroachDB Serverless.
- **Regions**: Multi-region deployment spanning `us-east-1` and `us-west-2`.
- **Purpose**: Unified ACID transactional state and high-dimensional semantic memory (vector embeddings).

## 2. Directory Layout
- **Migration Tool**: `dbmate`
- **Location**: `db/migrations/`
- **Deviation**: Blueprint originally specified `database/schema.sql`. We use `db/migrations/01_init.sql` to align with `dbmate` best practices.

## 3. Data Model

### `developer_accounts`
- `developer_id` UUID PRIMARY KEY
- `paddle_customer_id` VARCHAR(255) UNIQUE
- `api_key_hash` VARCHAR(64) UNIQUE NOT NULL
- `plan_tier` VARCHAR(50) DEFAULT 'free'

### `agent_sessions`
- `session_id` UUID PRIMARY KEY
- `developer_id` UUID (FK to `developer_accounts`)
- `agent_external_id` VARCHAR(255) NOT NULL
- `session_metadata` JSONB
- UNIQUE(`developer_id`, `agent_external_id`)

### `agent_transactional_state`
- `session_id` UUID (FK to `agent_sessions`)
- `state_key` VARCHAR(255) NOT NULL
- `state_value` JSONB NOT NULL
- `version_id` INT DEFAULT 1
- PRIMARY KEY (`session_id`, `state_key`)

### `agent_semantic_memory`
- `memory_id` UUID PRIMARY KEY
- `session_id` UUID (FK to `agent_sessions`)
- `raw_content` TEXT NOT NULL
- `embedding` VECTOR(1024) (Matched to Amazon Titan Text Embeddings V2)
- `token_count` INT DEFAULT 0
- Index: `semantic_memory_hnsw_idx` ON `agent_semantic_memory` USING `hnsw` (`embedding vector_cosine_ops`)

## 4. Setup Constraints
- Require pgvector extension (`CREATE EXTENSION IF NOT EXISTS vector;`).
- Must run as CockroachDB valid DDL.
