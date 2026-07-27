import os
import psycopg2
from psycopg2.extras import RealDictCursor
from lambda_function import generate_embedding_coordinates, get_db_connection

def execute_semantic_context_retrieval(session_id, search_query_string, match_limit=5):
    """
    Retrieves both the active transactional state variables and relevant semantic
    memories (using Cosine Distance search) for an agent session.
    """
    query_vector_coordinates = generate_embedding_coordinates(search_query_string)
    
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
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

    formatted_semantic_matches = []
    for match in semantic_historical_matches:
        match_dict = dict(match)
        if hasattr(match_dict.get("created_at"), "isoformat"):
            match_dict["created_at"] = match_dict["created_at"].isoformat()
        formatted_semantic_matches.append(match_dict)
        
    return {
        "transactional_state_context": {row["state_key"]: row["state_value"] for row in active_operational_states},
        "semantic_memory_history": formatted_semantic_matches
    }

