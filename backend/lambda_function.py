import os
import json
import hashlib
import psycopg2
import boto3
from psycopg2.extras import RealDictCursor

db_url = os.environ.get("COCKROACH_DB_URL", "postgresql://user:pass@localhost:26257/defaultdb")
conn = None

def get_db_connection():
    global conn
    try:
        if conn is None or conn.closed:
            conn = psycopg2.connect(db_url, application_name="statevault_dual_sync_engine")
        else:
            try:
                with conn.cursor() as test_cur:
                    test_cur.execute("SELECT 1")
            except Exception:
                if conn and not conn.closed:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                conn = psycopg2.connect(db_url, application_name="statevault_dual_sync_engine")
    except Exception:
        conn = psycopg2.connect(db_url, application_name="statevault_dual_sync_engine")
    return conn

current_region = os.environ.get("AWS_REGION", "us-east-1")
bedrock_client = boto3.client(service_name="bedrock-runtime", region_name=current_region)
sqs_client = boto3.client(service_name="sqs", region_name=current_region)

aws_account = os.environ.get("AWS_ACCOUNT_ID", "000000000000")
billing_queue_url = os.environ.get(
    "SQS_QUEUE_URL", 
    f"https://sqs.{current_region}.amazonaws.com/{aws_account}/statevault-billing-queue-{current_region}"
)

def generate_embedding_coordinates(text_content):
    payload = json.dumps({
        "inputText": text_content,
        "dimensions": 1024,
        "normalize": True
    })
    
    response = bedrock_client.invoke_model(
        body=payload,
        modelId="amazon.titan-embed-text-v2:0",
        accept="application/json",
        contentType="application/json"
    )
    
    response_body = json.loads(response["body"].read().decode("utf-8"))
    return response_body["embedding"]

def handler(event, context):
    try:
        headers = {k.lower(): v for k, v in event.get("headers", {}).items()} if event and event.get("headers") else {}
        api_key = headers.get("x-api-key")
        if not api_key:
            return {
                "statusCode": 401,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Unauthorized. Missing API Authorization Header."})
            }

        connection = get_db_connection()
        
        api_key_hash = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
        payload = json.loads(event.get("body", "{}"))
        
        agent_external_id = payload["agent_id"]
        state_key = payload["state_key"]
        state_value = payload["state_value"]
        raw_text_memory = payload["raw_text_memory"]
        
        vector_embedding = generate_embedding_coordinates(raw_text_memory)
        
        with connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT developer_id, paddle_customer_id, plan_tier FROM developer_accounts WHERE api_key_hash = %s", (api_key_hash,))
            dev_record = cur.fetchone()
            if not dev_record:
                return {
                    "statusCode": 403,
                    "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                    "body": json.dumps({"error": "Forbidden. Developer Tenant Verification Failed."})
                }
            
            dev_id = dev_record["developer_id"]
            paddle_cust_id = dev_record["paddle_customer_id"]
            plan_tier = dev_record["plan_tier"]
            
            cur.execute('''
                INSERT INTO agent_sessions (developer_id, agent_external_id, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (developer_id, agent_external_id) 
                DO UPDATE SET updated_at = NOW() RETURNING session_id;
            ''', (dev_id, agent_external_id))
            session_id = cur.fetchone()["session_id"]
            
            cur.execute('''
                INSERT INTO agent_transactional_state (session_id, state_key, state_value, version_id, updated_at)
                VALUES (%s, %s, %s::JSONB, 1, NOW())
                ON CONFLICT (session_id, state_key)
                DO UPDATE SET state_value = EXCLUDED.state_value, version_id = agent_transactional_state.version_id + 1, updated_at = NOW();
            ''', (session_id, state_key, json.dumps(state_value)))
            
            cur.execute('''
                INSERT INTO agent_semantic_memory (session_id, raw_content, embedding)
                VALUES (%s, %s, %s::VECTOR);
            ''', (session_id, raw_text_memory, str(vector_embedding)))
            
            connection.commit()
            
        if plan_tier != "free" and paddle_cust_id:
            try:
                sqs_client.send_message(
                    QueueUrl=billing_queue_url,
                    MessageBody=json.dumps({"paddle_customer_id": paddle_cust_id, "units": 1})
                )
            except Exception as sqs_err:
                print(f"Warning: Failed to enqueue billing record: {sqs_err}")
            
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"status": "success", "session_id": str(session_id), "synchronized": True})
        }
        
    except Exception as e:
        if 'connection' in locals() and connection and not connection.closed:
            connection.rollback()
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)})
        }
