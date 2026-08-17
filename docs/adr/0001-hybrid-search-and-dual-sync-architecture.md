# 0001. Hybrid Search and Dual-Sync Architecture

StateVault unifies ACID transactional state (JSONB) and high-dimensional semantic vectors (1024d pgvector) into a single CockroachDB transaction to eliminate split-brain data corruption across autonomous agent fleets. We combine native pgvector HNSW indexing with stored tsvector columns for Reciprocal Rank Fusion (RRF) hybrid recall, and provide a LangGraph CockroachDBSaver checkpointer bridge with row-level TTL for standard ecosystem compatibility.
