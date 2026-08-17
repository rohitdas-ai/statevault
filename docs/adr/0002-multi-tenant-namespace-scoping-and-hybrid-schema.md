# 0002. Multi-Tenant Namespace Scoping and Hybrid Schema

Multi-tenant isolation uses compound namespace strings (`<developer_id>:<agent_external_id>:<namespace>`) with CockroachDB prefix column indexing instead of dynamic per-tenant schemas to minimize DDL overhead. Semantic hybrid search utilizes a generated `TSVECTOR` column with GIN and HNSW indexes directly on `agent_semantic_memory` for zero-overhead index synchronization.
