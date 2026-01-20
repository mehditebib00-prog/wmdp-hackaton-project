import os
from openai import OpenAI
import requests


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def run_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content

def run_local_ollama(prompt):
    r = requests.post(
        "http://host.docker.internal:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    return r.json()["response"]

def run_model(model_name, prompt):
    if model_name == "openai":
        return run_openai(prompt)
    elif model_name == "ollama":
        return run_local_ollama(prompt)
    else:
        raise ValueError("Unknown model")
