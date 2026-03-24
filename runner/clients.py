import time
from transformers import pipeline

hf_models = {
    "mistral": pipeline(
        "text-generation",
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    ),
    "phi": pipeline(
        "text-generation",
        model="microsoft/phi-2",
    ),
    "judge": pipeline(
        "text-generation",
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    )
}

SYSTEM_PROMPT = """You are a precise and factual AI assistant.
- Be concise
- Avoid hallucinations
- If unsure, say you don't know
- Prefer clear structured answers
"""

def build_prompt(user_prompt):
    return f"{SYSTEM_PROMPT}\n\nUser: {user_prompt}\nAssistant:"

def retrieve_context(prompt):
    context = []

    with open("results.jsonl") as f:
        for line in f:
            item = json.loads(line)

            if item["score"] >= 8: 
                if prompt.lower() in item["question"].lower():
                    context.append(item["response"])

    return "\n".join(context[:2]) 

def call_model(prompt, model_name):
    start = time.time()
    model_name = model_name.lower()

    generator = hf_models[model_name]

    context = retrieve_context(prompt)
    full_prompt = build_prompt(prompt)

    if context:
        full_prompt = f"Context:\n{context}\n\n{full_prompt}"

    if model_name == "mistral":
        full_prompt = f"<s>[INST] {full_prompt} [/INST]"

    response = generator(
        full_prompt,
        max_new_tokens=150,
        do_sample=True,
        temperature=0.3,
        top_p=0.9,
        repetition_penalty=1.1
    )

    full_text = response[0]["generated_text"]
    text = full_text[len(full_prompt):].strip()

    latency = time.time() - start

    return {
        "response": text,
        "latency": latency,
        "input_tokens": len(full_prompt.split()),
        "output_tokens": len(text.split())
    }


def judge_responses(question, answer_a, answer_b):
    judge_prompt = f"""
You are an expert evaluator.

Question:
{question}

Answer A:
{answer_a}

Answer B:
{answer_b}

Which answer is better and why?
Respond in JSON:
{{
    "winner": "A" or "B",
    "reason": "short explanation",
    "score_a": 0-10,
    "score_b": 0-10
}}
"""

    result = hf_models["judge"](
        judge_prompt,
        max_new_tokens=200,
        temperature=0.2
    )

    text = result[0]["generated_text"][len(judge_prompt):].strip()

    return text