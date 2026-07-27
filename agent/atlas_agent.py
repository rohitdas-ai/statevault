import os
import requests

STATEVAULT_API = os.environ.get("STATEVAULT_API_URL", "https://api.statevault.site/v1/sync")
API_KEY = os.environ.get("STATEVAULT_API_KEY", "statevault_test_token_secret_abc")

class AtlasAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.state = {"step": 0, "status": "initialized", "tasks_completed": []}

    def execute_task(self, task_name, memory_text):
        print(f"[{self.agent_id}] Executing task: {task_name}")
        self.state["step"] += 1
        self.state["tasks_completed"].append(task_name)
        self.state["status"] = "processing"
        
        self._sync_memory(memory_text)
        
    def _sync_memory(self, text):
        payload = {
            "agent_id": self.agent_id,
            "state_key": "active_workflow_state",
            "state_value": self.state,
            "raw_text_memory": text
        }
        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        
        try:
            response = requests.post(STATEVAULT_API, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"[{self.agent_id}] Memory synced to CockroachDB successfully.")
            else:
                print(f"[{self.agent_id}] Response: {response.text}")
        except Exception as e:
            print(f"[{self.agent_id}] Network Exception: {str(e)}")

if __name__ == "__main__":
    agent = AtlasAgent("atlas_prod_01")
    agent.execute_task("analyze_logs", "Found anomalous login spikes in us-east-1.")
    agent.execute_task("block_ip", "Blocked IP range 192.168.1.0/24 due to suspicious activity.")
