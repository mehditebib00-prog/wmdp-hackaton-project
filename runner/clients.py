import os
import time
from enum import auto
from http.client import responses

from transformers import pipeline


hf_models = {
    "mistral": pipeline(
        "text-generation",
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        device_map="auto"
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

    generator = hf_models[model_name]

    if model_name == "mistral":
        prompt = f"<s>[INST] {prompt} [/INST]"

    response = generator(
        prompt,
        max_new_tokens=100,  
        do_sample=True,
        temperature=0.1,
        top_p=0.9,
        repetition_penalty=1.2
    )

    full_text = response[0]["generated_text"]

    text = full_text[len(prompt):].strip()

    latency = time.time() - start

    return {
        "response": text,
        "latency": latency
    }