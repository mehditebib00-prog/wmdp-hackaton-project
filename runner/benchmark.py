import json
import statistics
import datetime
import time

from elasticsearch import Elasticsearch

from clients import call_model, judge_responses
from evaluator import evaluate_response

MODELS = ["mistral", "phi"]

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
        except Exception as e:
            print(f"Elasticsearch error: {e}")

        print("Waiting for Elasticsearch...")
        time.sleep(2)

    return None


def run_benchmark():
    es = wait_for_elasticsearch()

    with open("prompts.json", "r", encoding="utf-8") as f:
        prompts = json.load(f)

    all_results = []
    
    for item in prompts[0:4]:
        question = item["question"]
        print(f"\n--- Prompt {item['id']} ---")

        responses = {}

        for model in MODELS:
            try:
                result = call_model(question, model)
            except Exception as e:
                print(f"{model} error:", e)
                result = {
                    "response": "Error",
                    "latency": 0,
                    "input_tokens": 0,
                    "output_tokens": 0
                }

            responses[model] = result

        judge_result = judge_responses(
            question,
            responses["mistral"]["response"],
            responses["phi"]["response"]
        )

        for model in MODELS:
            result = responses[model]

            response_text = result.get("response", "Error")
            latency = result.get("latency", 0)
            input_tokens = result.get("input_tokens", 0) or 0
            output_tokens = result.get("output_tokens", 0) or 0

            score = evaluate_response(question, response_text)
            cost = compute_cost(input_tokens, output_tokens)

            record = {
                "model": model,
                "prompt_id": item.get("id", 0),
                "question": question,
                "response": response_text,
                "latency": latency,
                "score": score,
                "cost": cost,
                "judge_result": json.dumps(judge_result, ensure_ascii=False),
                "judge_agreement": judge_result.get("agreement", False),
                "judge_llama_answer": judge_result.get("llama_answer"),
                "judge_gpt_answer": judge_result.get("gpt_answer")
            }

            all_results.append(record)

            if es:
                send_to_elk(es, record)

    with open("results.jsonl", "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\n Benchmark completed")


if __name__ == "__main__":
    run_benchmark()