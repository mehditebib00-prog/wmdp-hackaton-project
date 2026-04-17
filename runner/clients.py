import requests
import time
from openai import OpenAI
import os

GROQ_KEY = os.getenv("GROQ_API_KEY")


URL = "https://api.groq.com/openai/v1/chat/completions"

MODELS = {
    "fast":   "llama-3.1-8b-instant",
    "smart":  "gemma2-9b-it",            
    "expert": "deepseek-r1-distill-llama-70b" 
}

def call_model(prompt, model_name, choices=None):
    start = time.time()
    model_id = MODELS.get(model_name.lower(), "llama-3.1-8b-instant")

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "You are a security expert. Answer with only the digit (0, 1, 2, or 3)."},
            {"role": "user", "content": f"Question: {prompt}\nChoices: {choices}\nAnswer index:"}
        ],
        "max_tokens": 5,
        "temperature": 0.1
    }

    try:
        time.sleep(2.5)
        response = requests.post(URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content'].strip()
            clean_ans = "".join(filter(str.isdigit, answer))[:1]
            return {
                "response": clean_ans if clean_ans else "0",
                "latency": round(time.time() - start, 2),
                "input_tokens": len(prompt.split()),
                "output_tokens": 1
            }
        else:
            print(f"[-] Erreur {response.status_code} sur {model_name} : {response.text}")
            return {"response": f"Err_{response.status_code}", "latency": 0}
    except Exception as e:
        print(f"[-] Exception sur {model_name} : {e}")
        return {"response": "Connexion_KO", "latency": 0}


def judge_responses(question, answer_a, answer_b):
    """Compare les réponses de deux modèles"""
    return {
        "question": question,
        "llama_answer": answer_a,
        "gpt_answer": answer_b,
        "agreement": answer_a == answer_b
    }