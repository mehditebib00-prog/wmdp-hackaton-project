import time
import random

def call_model(prompt: str, model_name: str):
    """
    Simule un appel API modèle.
    Remplace par ton appel OpenAI / autre provider.
    """

    # Simulation latence variable
    simulated_latency = random.uniform(0.5, 1.5)
    time.sleep(simulated_latency)

    # Simulation réponse
    response = f"[{model_name}] Response to: {prompt}"

    # Simulation token usage
    input_tokens = len(prompt.split())
    output_tokens = random.randint(20, 60)

    return {
        "response": response,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency": simulated_latency
    }