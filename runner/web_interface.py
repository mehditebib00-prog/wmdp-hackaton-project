from flask import Flask, request, render_template_string
import difflib
import json

from clients import call_model, judge_responses

app = Flask(__name__)

MODELS = ["mistral", "phi"]

# Load prompts
with open("prompts.json", "r", encoding="utf-8") as f:
    PROMPTS = json.load(f)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Response Diff</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .response-box {
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            background-color: #f9f9f9;
        }
        .winner {
            border: 2px solid #28a745 !important;
            background-color: #eafaf1;
        }
        .diff-container {
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center mb-4"> AI Response Diff + Judge</h1>

        <form method="POST" action="/run">
            <div class="mb-3">
                <label class="form-label">Select a prompt:</label>
                <select class="form-control" name="prompt_id">
                    <option value="">-- Select from JSON --</option>
                    {% for prompt in prompts %}
                    <option value="{{ prompt.id }}">{{ prompt.id }}: {{ prompt.question[:50] }}...</option>
                    {% endfor %}
                </select>
            </div>

            <div class="mb-3">
                <label class="form-label">Or custom prompt:</label>
                <textarea class="form-control" name="custom_prompt" rows="4"></textarea>
            </div>

            <button type="submit" class="btn btn-primary">Run Diff</button>
        </form>

        {% if responses %}
        <div class="diff-container">

            <h2>Selected Prompt</h2>
            <p class="alert alert-info">{{ selected_prompt }}</p>

            <!-- Judge Result -->
            {% if judge %}
            <div class="alert alert-warning">
                <h4> Winner: {{ judge.winner }}</h4>
                <p><strong>Reason:</strong> {{ judge.reason }}</p>
                <p>
                    Score Mistral: {{ judge.score_a }} |
                    Score Phi: {{ judge.score_b }}
                </p>
            </div>
            {% endif %}

            <h2>Responses</h2>
            {% for model, response in responses.items() %}
            <div class="response-box 
                {% if judge and (
                    (judge.winner == 'A' and model == 'mistral') or
                    (judge.winner == 'B' and model == 'phi')
                ) %}winner{% endif %}">
                
                <h4>{{ model.capitalize() }}</h4>
                <p>{{ response }}</p>
            </div>
            {% endfor %}

            <h2>Differences</h2>
            <div class="diff-box">
                {{ diff_html|safe }}
            </div>

        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(
        HTML_TEMPLATE,
        responses=None,
        diff_html=None,
        prompts=PROMPTS,
        selected_prompt=None,
        judge=None
    )

@app.route('/run', methods=['POST'])
def run():
    prompt_id = request.form.get('prompt_id', '').strip()
    custom_prompt = request.form.get('custom_prompt', '').strip()

    if prompt_id:
        selected_prompt_obj = next(p for p in PROMPTS if str(p['id']) == prompt_id)
        prompt = selected_prompt_obj['question']
        selected_prompt = f"JSON Prompt {prompt_id}: {prompt}"
    elif custom_prompt:
        prompt = custom_prompt
        selected_prompt = f"Custom Prompt: {prompt}"
    else:
        return "Please select a JSON prompt or enter a custom prompt.", 400

    responses = {}


    for model in MODELS:
        try:
            result = call_model(prompt, model)
            responses[model] = result['response']
        except Exception as e:
            responses[model] = f"Error: {str(e)}"

    judge_data = None
    try:
        raw_judge = judge_responses(
            prompt,
            responses["mistral"],
            responses["phi"]
        )

        import json as _json
        try:
            judge_data = _json.loads(raw_judge)
        except:
            judge_data = {
                "winner": "Unknown",
                "reason": raw_judge,
                "score_a": "-",
                "score_b": "-"
            }

    except Exception as e:
        judge_data = {
            "winner": "Error",
            "reason": str(e),
            "score_a": "-",
            "score_b": "-"
        }

    # Generate diff
    model1, model2 = list(responses.keys())
    diff = difflib.HtmlDiff()
    diff_html = diff.make_table(
        responses[model1].splitlines(),
        responses[model2].splitlines(),
        fromdesc=model1.capitalize(),
        todesc=model2.capitalize()
    )

    return render_template_string(
        HTML_TEMPLATE,
        responses=responses,
        diff_html=diff_html,
        prompts=PROMPTS,
        selected_prompt=selected_prompt,
        judge=judge_data
    )

if __name__ == '__main__':
    app.run(debug=True)