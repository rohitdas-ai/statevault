# StateVault Core

Resilient multi-region memory layer providing atomic transactional and high-dimensional semantic persistence for autonomous AI agent networks.

## Language

**Dual-Sync**:
An atomic database transaction committing structured operational state (JSONB) and high-dimensional semantic embeddings (pgvector) together in a single roundtrip.
_Avoid_: Two-phase write, split write, background indexer

**Transactional State**:
ACID-compliant operational variables and task execution metadata stored as JSONB with row-level optimistic versioning.
_Avoid_: App state, session cache, runtime dict

**Semantic Memory**:
High-dimensional text embeddings stored with vector indexing (HNSW / C-SPANN cosine distance) for contextual similarity search.
_Avoid_: Vector store, knowledge base, RAG doc

**Hybrid Recall**:
Parallel execution of cosine vector similarity search and full-text keyword search (`to_tsvector`) fused via Reciprocal Rank Fusion (RRF with k=60).
_Avoid_: Keyword search, raw vector query, full-text match

**Checkpointer Bridge**:
A persistent LangGraph state saver (`CockroachDBSaver`) integrated directly into CockroachDB with configurable row-level TTL for agent execution history.
_Avoid_: Memory saver, session dump, graph cache

**Dual-Tier Retention**:
Data lifecycle policy applying Row-Level TTL (14 days) to ephemeral execution traces while preserving operational state and semantic memory indefinitely.
_Avoid_: Global purge, hard delete, manual pruning

**Namespace Scoping**:
Multi-tenant isolation pattern prefixing agent identifiers (`<developer_id>:<agent_external_id>:<namespace>`) onto checkpointer keys and database queries for prefix index pushdown.
_Avoid_: Tenant schema, database partition, isolated DB

**Deterministic Vector Fallback**:
Offline 1024-dimensional normalized coordinate generator enabling test suites and judge evaluation without live AWS IAM credentials.
_Avoid_: Dummy vector, zero vector, random embedding

**Agent Session**:
Unique execution lifecycle for an autonomous agent instance belonging to a tenant developer account.
_Avoid_: Connection, thread, conversation

**Split-Brain Desynchronization**:
Failure mode where separate transactional and vector stores experience partial write failure, causing irreversible memory corruption and agent hallucinations.
_Avoid_: Race condition, network lag, drift
