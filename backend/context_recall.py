import os
import psycopg2
from psycopg2.extras import RealDictCursor
from lambda_function import generate_embedding_coordinates

db_url = os.environ.get("COCKROACH_DB_URL", "postgresql://user:pass@localhost:26257/defaultdb")

def execute_semantic_context_retrieval(session_id, search_query_string, match_limit=5):
    """
    Retrieves both the active transactional state variables and relevant semantic
    memories (using Cosine Distance search) for an agent session.
    """
    query_vector_coordinates = generate_embedding_coordinates(search_query_string)
    
    read_conn = psycopg2.connect(db_url, application_name="statevault_read_engine")
    try:
        with read_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT state_key, state_value FROM agent_transactional_state WHERE session_id = %s", (session_id,))
            active_operational_states = cur.fetchall()
            
            cur.execute('''
                SELECT raw_content, created_at, (embedding <=> %s::VECTOR) as spatial_distance_score 
                FROM agent_semantic_memory 
                WHERE session_id = %s
                ORDER BY embedding <=> %s::VECTOR ASC 
                LIMIT %s;
            ''', (str(query_vector_coordinates), session_id, str(query_vector_coordinates), match_limit))
            semantic_historical_matches = cur.fetchall()
            
        return {
            "transactional_state_context": {row["state_key"]: row["state_value"] for row in active_operational_states},
            "semantic_memory_history": semantic_historical_matches
        }
    finally:
        read_conn.close()
