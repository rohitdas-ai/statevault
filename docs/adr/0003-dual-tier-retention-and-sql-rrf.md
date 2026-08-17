# 0003. Dual-Tier Retention and In-Database Reciprocal Rank Fusion

StateVault executes hybrid search directly within CockroachDB using a SQL CTE implementing Reciprocal Rank Fusion (RRF k=60) across parallel HNSW vector cosine distance and GIN tsvector scans. To manage storage lifecycle without manual DBA maintenance, ephemeral LangGraph checkpoints use CockroachDB Row-Level TTL (14-day expiry), while core semantic memories and operational state remain persistent.
