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
