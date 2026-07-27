# StateVault

Resilient, Multi-Region Memory-as-a-Service for Autonomous AI Agent Networks built on CockroachDB & AWS.

## Architecture
StateVault unifies ACID transactional state (`JSONB`) and high-dimensional semantic memory (`pgvector`) into a single atomic CockroachDB transaction block.

## Quickstart
1. Copy `env.local` to `.env` and fill in credentials.
2. Run database migration: `psql $COCKROACH_DB_URL -f database/schema.sql`
3. Execute agent test harness: `python agent/atlas_agent.py`
4. Deploy serverless stack: `sam build && sam deploy --guided`
