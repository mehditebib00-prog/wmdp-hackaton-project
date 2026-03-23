import json
import statistics
import datetime
import time
from logging import exception

from elasticsearch import Elasticsearch
from sympy.codegen.ast import none

from clients import call_model
from evaluator import evaluate_response

MODELS = [
    "mistral",
    "phi"
]

INPUT_PRICE = 0.00001
OUTPUT_PRICE = 0.00002
ELASTIC_INDEX = "wmdp-security-benchmark"


def compute_cost(input_tokens, output_tokens):
    return (input_tokens * INPUT_PRICE) + (output_tokens * OUTPUT_PRICE)


def send_to_elk(es_client, data):
    try:
        es_client.index(
            index=ELASTIC_INDEX,
            document={
                **data,
                "timestamp": datetime.datetime.utcnow()
            }
        )
    except Exception as e:
        print("ELK Error:", e)


def wait_for_elasticsearch(url="http://localhost:9200", timeout=60):
    es = Elasticsearch(
        url,
        verify_certs=False,
        ssl_show_warn=False,
        request_timeout=30,
        basic_auth=("elastic", "changeme123")
    )

    start = time.time()
    while time.time() - start < timeout:
        try:
            if es.ping():
                print("Connected to Elasticsearch")
                return es
            else:
                # Add this — ping() swallows errors, info() won't
                info = es.info()
                print("Connected but ping returned False?", info)
                return es
        except Exception as e:
            print(f"Elasticsearch error: {type(e).__name__}: {e}")

        print("Waiting for Elasticsearch...")
        time.sleep(2)


def run_benchmark():
    es = wait_for_elasticsearch()

    with open("prompts.json", "r", encoding="utf-8") as f:
        prompts = json.load(f)

    all_results = []

    for model in MODELS:
        print(f"\n--- Running benchmark for {model} ---")

        latencies = []
        scores = []
        costs = []

        for item in prompts:
            question = item["question"]

            try:
                # Only pass valid generation args; avoid deprecated warnings
                result = call_model(question, model)
                result.setdefault("input_tokens", 0)
                result.setdefault("output_tokens", 0)
                result.setdefault("latency", 0)
                result.setdefault("response", "Refused or error")
            except Exception as e:
                print(f"Error on prompt {item['id']}: {e}")
                result = {
                    "response": "Refused or error",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "latency": 0
                }

            score = evaluate_response(question, result["response"])
            cost = compute_cost(result["input_tokens"], result["output_tokens"])

            latencies.append(result["latency"])
            scores.append(score)
            costs.append(cost)

            record = {
                "model": model,
                "prompt_id": item["id"],
                "question": question,
                "response": result["response"],
                "latency": result["latency"],
                "score": score,
                "cost": cost
            }

            all_results.append(record)

            if es:
                send_to_elk(es, record)

        print("Average latency:", round(statistics.mean(latencies), 3))
        print("Average score:", round(statistics.mean(scores), 3))
        print("Total cost:", round(sum(costs), 6))

    with open("results.jsonl", "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\nBenchmark completed")


if __name__ == "__main__":
    run_benchmark()