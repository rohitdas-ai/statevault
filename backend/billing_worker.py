import os
import json
import requests

def handler(event, context):
    paddle_api_key = os.environ.get("PADDLE_API_KEY", "")
    price_id = os.environ.get("PADDLE_PRODUCT_PRICE_ID", "")
    
    aggregated_usage = {}
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        cust_id = body["paddle_customer_id"]
        units = body["units"]
        aggregated_usage[cust_id] = aggregated_usage.get(cust_id, 0) + units
        
    failed_customers = []
    
    for customer_id, total_units in aggregated_usage.items():
        url = "https://sandbox-api.paddle.com/transactions"
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
            response = requests.post(url, json=data, headers=headers, timeout=5)
            response.raise_for_status()
        except Exception as e:
            print(f"Paddle Sync Error for customer {customer_id}: {str(e)}")
            failed_customers.append(customer_id)
            
    if failed_customers:
        print(f"Warning: Failed to bill the following customers in batch: {failed_customers}")
        
    return {
        "status": "partial_success" if failed_customers else "success",
        "processed_clients": len(aggregated_usage) - len(failed_customers)
    }
