import os
import time
from enum import auto

from transformers import pipeline


hf_models = {
    "mistral": pipeline(
        "text-generation",
        model="mistralai/Mistral-7B-Instruct-v0.2",
        device=0
    ),

    "phi": pipeline(
        "text-generation",
        model="microsoft/phi-2",
        device_map="auto"
    )
}

def call_model(prompt, model_name):
    start = time.time()
    model_name = model_name.lower()

    if model_name not in hf_models:
        raise ValueError(f"Unknown model: {model_name}")

    generator = hf_models[model_name]

    response = generator(prompt, max_new_tokens=150)
    text = response[0]["generated_text"]
    if not text :
        print("No response from model")

    latency = time.time() - start

    input_tokens = len(prompt.split())
    output_tokens = len(text.split())

    return {
        "response": text.strip(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency": latency
    }