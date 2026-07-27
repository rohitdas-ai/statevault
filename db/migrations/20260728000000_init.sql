-- migrate:up
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE developer_accounts (
    developer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paddle_customer_id VARCHAR(255) UNIQUE,
    api_key_hash VARCHAR(64) UNIQUE NOT NULL,
    plan_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    developer_id UUID REFERENCES developer_accounts(developer_id) ON DELETE CASCADE,
    agent_external_id VARCHAR(255) NOT NULL,
    session_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(developer_id, agent_external_id)
);

CREATE TABLE agent_transactional_state (
    session_id UUID REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    state_key VARCHAR(255) NOT NULL,
    state_value JSONB NOT NULL,
    version_id INT DEFAULT 1,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (session_id, state_key)
);

CREATE TABLE agent_semantic_memory (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    raw_content TEXT NOT NULL,
    embedding VECTOR(1024),
    token_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS semantic_memory_hnsw_idx 
ON agent_semantic_memory USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS semantic_memory_session_id_idx ON agent_semantic_memory(session_id);

-- migrate:down
DROP TABLE IF EXISTS agent_semantic_memory CASCADE;
DROP TABLE IF EXISTS agent_transactional_state CASCADE;
DROP TABLE IF EXISTS agent_sessions CASCADE;
DROP TABLE IF EXISTS developer_accounts CASCADE;
