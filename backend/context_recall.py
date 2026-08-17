import os
import psycopg2
from psycopg2.extras import RealDictCursor
from lambda_function import generate_embedding_coordinates, get_db_connection

def execute_semantic_context_retrieval(session_id, search_query_string, match_limit=5):
    """
    Retrieves both the active transactional state variables and relevant semantic
    memories using in-database Reciprocal Rank Fusion (RRF k=60) combining pgvector
    cosine proximity and GIN tsvector full-text keyword ranking.
    """
    query_vector_coordinates = generate_embedding_coordinates(search_query_string)
    
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT state_key, state_value FROM agent_transactional_state WHERE session_id = %s", (session_id,))
        active_operational_states = cur.fetchall()
        
        hybrid_query = """
            WITH vec AS (
                SELECT memory_id, ROW_NUMBER() OVER (ORDER BY embedding <=> %s::VECTOR) as r_vec
                FROM agent_semantic_memory 
                WHERE session_id = %s
                LIMIT 50
            ),
            txt AS (
                SELECT memory_id, ROW_NUMBER() OVER (ORDER BY ts_rank(tsv, plainto_tsquery('english', %s)) DESC) as r_txt
                FROM agent_semantic_memory 
                WHERE session_id = %s AND tsv @@ plainto_tsquery('english', %s)
                LIMIT 50
            )
            SELECT m.memory_id, m.raw_content, m.created_at,
                   (COALESCE(1.0 / (60 + vec.r_vec), 0.0) + COALESCE(1.0 / (60 + txt.r_txt), 0.0)) AS rrf_score
            FROM agent_semantic_memory m
            LEFT JOIN vec ON m.memory_id = vec.memory_id
            LEFT JOIN txt ON m.memory_id = txt.memory_id
            WHERE (vec.memory_id IS NOT NULL OR txt.memory_id IS NOT NULL)
              AND m.session_id = %s
            ORDER BY rrf_score DESC
            LIMIT %s;
        """
        try:
            cur.execute(hybrid_query, (
                str(query_vector_coordinates), session_id,
                search_query_string, session_id, search_query_string,
                session_id, match_limit
            ))
            semantic_historical_matches = cur.fetchall()
        except Exception:
            conn.rollback()
            cur.execute('''
                SELECT memory_id, raw_content, created_at, (1.0 - (embedding <=> %s::VECTOR)) as rrf_score 
                FROM agent_semantic_memory 
                WHERE session_id = %s
                ORDER BY embedding <=> %s::VECTOR ASC 
                LIMIT %s;
            ''', (str(query_vector_coordinates), session_id, str(query_vector_coordinates), match_limit))
            semantic_historical_matches = cur.fetchall()

    formatted_semantic_matches = []
    for match in semantic_historical_matches:
        match_dict = dict(match)
        if hasattr(match_dict.get("created_at"), "isoformat"):
            match_dict["created_at"] = match_dict["created_at"].isoformat()
        if "memory_id" in match_dict and match_dict["memory_id"] is not None:
            match_dict["memory_id"] = str(match_dict["memory_id"])
        formatted_semantic_matches.append(match_dict)
        
    return {
        "transactional_state_context": {row["state_key"]: row["state_value"] for row in active_operational_states},
        "semantic_memory_history": formatted_semantic_matches
    }

execute_hybrid_context_retrieval = execute_semantic_context_retrieval
