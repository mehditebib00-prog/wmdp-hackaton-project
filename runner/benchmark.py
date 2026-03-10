import json
import statistics
import datetime
from elasticsearch import Elasticsearch
from clients import call_model
from evaluator import evaluate_response

MODELS = ["model-A", "model-B"]
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

def run_benchmark():
    try:
        es = Elasticsearch("http://localhost:9200")
        if not es.ping():
            print("⚠ Elasticsearch not reachable")
            es = None
        else:
            print("Connected to Elasticsearch")
    except Exception as e:
        print("Elasticsearch connection failed:", e)
        es = None

    with open("prompts.json", "r", encoding="utf-8") as f:
        prompts = json.load(f)

    all_results = []

    for model in MODELS:
        print(f"\nRunning benchmark for {model}")
        latencies = []
        scores = []
        costs = []

        for item in prompts:
            question = item["question"]

            try:
                result = call_model(question, model)
                if result is None or "response" not in result:
                    result = {"response": "Refused or error", "input_tokens": 0, "output_tokens": 0, "latency": 0}
            except Exception as e:
                print(f"Erreur sur la question {item['id']}: {e}")
                result = {"response": "Refused or error", "input_tokens": 0, "output_tokens": 0, "latency": 0}

            try:
                score = evaluate_response(question, result["response"])
            except Exception as e:
                print(f"Erreur d'évaluation sur la question {item['id']}: {e}")
                score = 0

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

        if latencies:
            print("Average latency:", round(statistics.mean(latencies), 3))
        if scores:
            print("Average score:", round(statistics.mean(scores), 3))
        print("Total cost:", round(sum(costs), 6))

    with open("results.jsonl", "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\nBenchmark completed")

if __name__ == "__main__":
    run_benchmark()