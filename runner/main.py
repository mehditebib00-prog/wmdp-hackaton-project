import json
import time
from datetime import datetime
from elasticsearch import Elasticsearch
from clients import run_model

# ===========================
# Elasticsearch setup
# ===========================
ES_HOST = "https://elasticsearch:9200"  # Docker service name if on same network
ES_USER = "elastic"
ES_PASS = "changeme123"
INDEX_NAME = "llm_responses"

# Connect to Elasticsearch with HTTPS + auth, ignoring self-signed certs
es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASS),
    verify_certs=False  # self-signed cert in Docker
)

# ===========================
# Models
# ===========================
MODELS = ["openai", "ollama"]

# ===========================
# Functions
# ===========================
def create_index():
    """Create the index if it doesn't exist."""
    if not es.indices.exists(index=INDEX_NAME):
        print(f"Creating index: {INDEX_NAME}")
        es.indices.create(
            index=INDEX_NAME,
            mappings={
                "properties": {
                    "prompt_id": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "model": {"type": "keyword"},
                    "response": {"type": "text"},
                    "timestamp": {"type": "date"}
                }
            }
        )
    else:
        print(f"Index {INDEX_NAME} already exists")

def load_prompts():
    """Load prompts from a JSON file."""
    with open("prompts.json") as f:
        return json.load(f)

def main():
    create_index()
    prompts = load_prompts()

    for prompt in prompts:
        for model in MODELS:
            print(f"[{datetime.utcnow()}] Running prompt '{prompt['id']}' on model '{model}'")

            try:
                response = run_model(model, prompt["prompt"])
            except Exception as e:
                response = f"ERROR: {e}"

            doc = {
                "prompt_id": prompt["id"],
                "category": prompt["category"],
                "model": model,
                "response": response,
                "timestamp": datetime.utcnow()
            }

            es.index(index=INDEX_NAME, document=doc)
            time.sleep(2)  # avoid rate limits

# ===========================
# Entry point
# ===========================
if __name__ == "__main__":
    main()
