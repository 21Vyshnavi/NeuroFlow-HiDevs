import random
from locust import HttpUser, task, between
from backend.security.auth import create_access_token

SAMPLE_QUERIES = [
    "What is the system architecture?",
    "How does hybrid search work?",
    "Explain the evaluations framework.",
    "What are the metrics for faithfulness?",
    "How to trigger fine-tuning?"
]

class QueryUser(HttpUser):
    weight = 7
    wait_time = between(1, 3)

    def on_start(self):
        token = create_access_token({"sub": "query_user", "scopes": ["query"]})
        self.headers = {"Authorization": f"Bearer {token}"}

    @task
    def query_pipeline(self):
        self.client.post(
            "/query",
            json={"query": random.choice(SAMPLE_QUERIES), "stream": False},
            headers=self.headers
        )

class IngestUser(HttpUser):
    weight = 2
    wait_time = between(2, 5)

    def on_start(self):
        token = create_access_token({"sub": "ingest_user", "scopes": ["ingest"]})
        self.headers = {"Authorization": f"Bearer {token}"}

    @task
    def ingest_document(self):
        # Ingest a simple small content or mock file
        files = {
            "file": ("test.txt", b"Mock document content for load testing", "text/plain")
        }
        self.client.post("/ingest", files=files, headers=self.headers)

class AdminUser(HttpUser):
    weight = 1
    wait_time = between(3, 8)

    def on_start(self):
        token = create_access_token({"sub": "admin_user", "scopes": ["query", "admin"]})
        self.headers = {"Authorization": f"Bearer {token}"}

    @task
    def check_evaluations(self):
        self.client.get("/evaluations", headers=self.headers)
