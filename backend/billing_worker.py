import os
import json
import requests

def handler(event, context):
    paddle_api_key = os.environ.get("PADDLE_API_KEY", "")
    price_id = os.environ.get("PADDLE_PRODUCT_PRICE_ID", "")
    paddle_api_url = os.environ.get("PADDLE_API_URL", "https://sandbox-api.paddle.com/transactions")
    
    # Map customer_id -> list of record messageIds
    customer_message_map = {}
    aggregated_usage = {}
    
    for record in event.get("Records", []):
        msg_id = record.get("messageId")
        try:
            body = json.loads(record["body"])
            cust_id = body["paddle_customer_id"]
            units = body["units"]
            aggregated_usage[cust_id] = aggregated_usage.get(cust_id, 0) + units
            if msg_id:
                customer_message_map.setdefault(cust_id, []).append(msg_id)
        except Exception as e:
            print(f"Error parsing record body: {str(e)}")
            
    batch_item_failures = []
    
    for customer_id, total_units in aggregated_usage.items():
        headers = {
            "Authorization": f"Bearer {paddle_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "status": "billed",
            "collection_mode": "manual",
            "customer_id": customer_id,
            "items": [{"price_id": price_id, "quantity": total_units}]
        }
        
        try:
            response = requests.post(paddle_api_url, json=data, headers=headers, timeout=5)
            response.raise_for_status()
        except Exception as e:
            print(f"Paddle Sync Error for customer {customer_id}: {str(e)}")
            for item_id in customer_message_map.get(customer_id, []):
                batch_item_failures.append({"itemIdentifier": item_id})
            
    return {
        "status": "partial_success" if batch_item_failures else "success",
        "processed_clients": len(aggregated_usage) - len(set(customer_id for customer_id, msgs in customer_message_map.items() if any({"itemIdentifier": m} in batch_item_failures for m in msgs))),
        "batchItemFailures": batch_item_failures
    }


