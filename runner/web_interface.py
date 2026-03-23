from flask import Flask, request, render_template_string
import difflib
from clients import call_model

app = Flask(__name__)

MODELS = ["mistral", "phi"]

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
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .diff-container {
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center mb-4">AI Response Diff Tool</h1>
        <form method="POST" action="/run">
            <div class="mb-3">
                <label for="prompt" class="form-label">Enter your prompt:</label>
                <textarea class="form-control" id="prompt" name="prompt" rows="4" placeholder="Type your prompt here..."></textarea>
            </div>
            <button type="submit" class="btn btn-primary">Run Diff</button>
        </form>
        {% if responses %}
        <div class="diff-container">
            <h2>Responses</h2>
            {% for model, response in responses.items() %}
            <div class="response-box">
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
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, responses=None, diff_html=None)

@app.route('/run', methods=['POST'])
def run():
    prompt = request.form['prompt']
    responses = {}
    for model in MODELS:
        try:
            result = call_model(prompt, model)
            responses[model] = result['response']
        except Exception as e:
            responses[model] = f"Error: {str(e)}"
    
    # Generate diff
    if len(responses) == 2:
        model1, model2 = list(responses.keys())
        diff = difflib.HtmlDiff()
        diff_html = diff.make_table(responses[model1].splitlines(), responses[model2].splitlines(), 
                                    fromdesc=model1.capitalize(), todesc=model2.capitalize())
    else:
        diff_html = "<p>Not enough responses to compare.</p>"
    
    return render_template_string(HTML_TEMPLATE, responses=responses, diff_html=diff_html)

if __name__ == '__main__':
    app.run(debug=True)