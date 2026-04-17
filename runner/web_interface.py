import datetime
import json
import os
import time
from flask import Flask, render_template_string, request, jsonify
from elasticsearch import Elasticsearch
from clients import call_model

app = Flask(__name__)

# --- CONFIGURATION ELASTICSEARCH ---
# Connexion à ton instance locale (assure-toi que Docker ou le service ES tourne)
try:
    es = Elasticsearch("http://localhost:9200")
    if es.ping():
        print("[+] Connecté à Elasticsearch pour le monitoring.")
    else:
        print("[-] Elasticsearch injoignable. Le Lab fonctionnera sans sauvegarde.")
        es = None
except Exception as e:
    print(f"[-] Erreur de connexion ES : {e}")
    es = None

ELASTIC_INDEX = "wmdp-security-benchmark"

# --- CHARGEMENT DU DATASET ---
PROMPTS = []
prompts_path = os.path.join(os.path.dirname(__file__), "prompts.json")
if os.path.exists(prompts_path):
    with open(prompts_path, "r", encoding="utf-8") as f:
        PROMPTS = json.load(f)
    print(f"[+] {len(PROMPTS)} questions chargées")

# --- TEMPLATE HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TreeTech — Security Lab</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        :root {
            --bg: #0c0e12; --bg2: #13161d; --bg3: #1a1e28;
            --border: #2a2f3d; --border-bright: #3d4459;
            --text: #e2e6f0; --text-muted: #7a8099; --text-dim: #4a5068;
            --accent: #4ade80; --accent-dim: #166534; --accent-glow: rgba(74, 222, 128, 0.12);
            --amber: #fbbf24; --blue: #60a5fa; --red: #f87171;
            --font-mono: 'JetBrains Mono', monospace; --font-display: 'Syne', sans-serif;
            --radius: 8px; --radius-lg: 12px;
        }
        body { font-family: var(--font-mono); background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; }
        header { border-bottom: 1px solid var(--border); padding: 0 2rem; height: 56px; display: flex; align-items: center; justify-content: space-between; background: var(--bg); position: sticky; top: 0; z-index: 10; }
        .logo { font-family: var(--font-display); font-weight: 800; font-size: 1.1rem; display: flex; align-items: center; gap: 10px; }
        .logo-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 8px var(--accent); animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .status-pill { font-size: 0.7rem; color: var(--accent); background: var(--accent-glow); border: 1px solid var(--accent-dim); padding: 3px 10px; border-radius: 99px; }
        .workspace { flex: 1; display: grid; grid-template-columns: 260px 1fr; height: calc(100vh - 56px); }
        .sidebar { border-right: 1px solid var(--border); padding: 1.5rem 1rem; display: flex; flex-direction: column; gap: 1.5rem; overflow-y: auto; }
        .sidebar-section-label { font-size: 0.65rem; color: var(--text-dim); letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.5rem; }
        .model-card { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: var(--radius); border: 1px solid var(--border); cursor: pointer; transition: all 0.15s; }
        .model-card:hover { border-color: var(--border-bright); background: var(--bg3); }
        .model-card.active { border-color: var(--accent-dim); background: var(--accent-glow); }
        .model-card input { display: none; }
        .model-icon { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 14px; background: var(--bg3); }
        .model-card.active .model-icon { background: var(--accent-dim); }
        .model-info { flex: 1; min-width: 0; }
        .model-name { font-size: 0.75rem; font-weight: 500; }
        .model-tag { font-size: 0.6rem; color: var(--text-muted); }
        .stat-box { background: var(--bg3); border: 1px solid var(--border); border-radius: var(--radius); padding: 10px; flex: 1; }
        .stat-val { font-size: 1.2rem; font-weight: 700; }
        .stat-label { font-size: 0.6rem; color: var(--text-dim); text-transform: uppercase; }
        .editor-pane { display: flex; flex-direction: column; overflow: hidden; }
        .editor-topbar { border-bottom: 1px solid var(--border); padding: 0.75rem 1.5rem; display: flex; align-items: center; gap: 12px; background: var(--bg2); }
        .nav-btn { width: 28px; height: 28px; border: 1px solid var(--border); background: transparent; color: var(--text-muted); border-radius: 6px; cursor: pointer; }
        .q-counter { font-size: 0.75rem; color: var(--text-muted); }
        .code-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; padding: 1.5rem; gap: 1rem; }
        .question-block { background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 1.25rem 1.5rem; }
        .q-label { font-size: 0.65rem; color: var(--accent); text-transform: uppercase; margin-bottom: 8px; }
        .input-wrapper { position: relative; flex: 1; }
        #codeInput { width: 100%; height: 100%; background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius-lg); color: var(--text); font-family: var(--font-mono); padding: 1rem 1rem 1rem 56px; resize: none; outline: none; }
        .line-numbers { position: absolute; left: 0; top: 0; bottom: 0; width: 44px; padding: 1rem 0; display: flex; flex-direction: column; align-items: flex-end; padding-right: 12px; color: var(--text-dim); font-size: 0.75rem; border-right: 1px solid var(--border); background: var(--bg2); border-radius: var(--radius-lg) 0 0 var(--radius-lg); }
        #runBtn { font-family: var(--font-mono); font-size: 0.8rem; font-weight: 700; padding: 10px 24px; border-radius: var(--radius); border: none; background: var(--accent); color: #0a1a10; cursor: pointer; }
        .output-pane { border-top: 1px solid var(--border); background: var(--bg); max-height: 50vh; overflow-y: auto; }
        .output-header { padding: 8px 1.5rem; border-bottom: 1px solid var(--border); background: var(--bg2); display: flex; align-items: center; justify-content: space-between; }
        .latency-chip { background: var(--bg3); border: 1px solid var(--border); border-radius: 99px; padding: 1px 8px; color: var(--amber); font-size: 0.65rem; }
        .output-body { padding: 1.5rem; }
        .answer-banner { background: rgba(74, 222, 128, 0.06); border: 1px solid var(--accent-dim); border-radius: var(--radius); padding: 12px; margin-bottom: 1rem; }
        .explanation-block { border-left: 2px solid var(--border); padding-left: 1rem; }
        .ex-text { font-size: 0.85rem; line-height: 1.75; color: var(--text-muted); white-space: pre-wrap; }
        .loading-line { height: 2px; background: linear-gradient(90deg, transparent, var(--accent), transparent); animation: scan 1.2s linear infinite; }
        @keyframes scan { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
    </style>
</head>
<body>

<header>
    <div class="logo"><div class="logo-dot"></div>TreeTech <span style="color: var(--text-dim); font-weight: 400;">/ Security Lab</span></div>
    <div class="status-pill">{{ total }} questions chargées</div>
</header>

<div class="workspace">
    <aside class="sidebar">
        <div>
            <div class="sidebar-section-label">Modèle</div>
            <div class="model-card active" id="card-fast" onclick="selectModel('fast')">
                <div class="model-icon">⚡</div>
                <div class="model-info"><div class="model-name">Llama 3.1 8B</div><div class="model-tag">fast · instant</div></div>
            </div>
            <div class="model-card" id="card-smart" onclick="selectModel('smart')" style="margin-top:6px;">
                <div class="model-icon">🧠</div>
                <div class="model-info"><div class="model-name">Gemma 2 9B</div><div class="model-tag">smart · balanced</div></div>
            </div>
            <div class="model-card" id="card-expert" onclick="selectModel('expert')" style="margin-top:6px;">
                <div class="model-icon">🔬</div>
                <div class="model-info"><div class="model-name">DeepSeek R1 70B</div><div class="model-tag">expert · reasoning</div></div>
            </div>
        </div>
        <div style="display:flex; gap:8px;">
            <div class="stat-box"><div class="stat-val" id="stat-run">0</div><div class="stat-label">analysées</div></div>
        </div>
    </aside>

    <div class="editor-pane">
        <div class="editor-topbar">
            <button class="nav-btn" onclick="prevQ()">←</button>
            <span class="q-counter">Question <span id="qNum">1</span> / {{ total }}</span>
            <button class="nav-btn" onclick="nextQ()">→</button>
        </div>
        <div class="code-area">
            <div class="question-block">
                <div class="q-label">// security threat scenario</div>
                <div class="q-text" id="questionText">Chargement...</div>
            </div>
            <div class="input-wrapper">
                <div class="line-numbers" id="lineNumbers"><span>1</span></div>
                <textarea id="codeInput" placeholder="# Analyse la menace ici..."></textarea>
            </div>
            <div class="run-bar">
                <button id="runBtn" onclick="askAI()">▶ Analyser avec l'IA</button>
            </div>
        </div>
        <div class="output-pane" id="outputPane" style="display:none;">
            <div class="output-header">
                <div style="font-size:0.7rem; text-transform:uppercase;">Analyse Result</div>
                <span class="latency-chip" id="latChip">0s</span>
            </div>
            <div class="output-body" id="outputBody"></div>
        </div>
    </div>
</div>

<script>
    const prompts = {{ prompts | tojson }};
    let currentIndex = 0;
    let selectedModel = 'fast';
    let runCount = 0;

    function selectModel(val) {
        selectedModel = val;
        document.querySelectorAll('.model-card').forEach(c => c.classList.remove('active'));
        document.getElementById('card-' + val).classList.add('active');
    }

    function loadQuestion(idx) {
        const q = prompts[idx];
        document.getElementById('questionText').textContent = q.question;
        document.getElementById('qNum').textContent = idx + 1;
        document.getElementById('outputPane').style.display = 'none';
        document.getElementById('codeInput').value = '';
    }

    function askAI() {
        const q = prompts[currentIndex];
        const userCode = document.getElementById('codeInput').value;
        const btn = document.getElementById('runBtn');
        btn.disabled = true;
        document.getElementById('outputPane').style.display = 'block';
        document.getElementById('outputBody').innerHTML = '<div class="loading-line"></div>';

        fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: q.question,
                user_code: userCode,
                answer: q.answer,
                choices: q.choices || [],
                model: selectedModel
            })
        })
        .then(r => r.json())
        .then(data => {
            btn.disabled = false;
            runCount++;
            document.getElementById('stat-run').textContent = runCount;
            document.getElementById('latChip').textContent = data.latency + 's';
            
            const correct = Array.isArray(q.choices) ? q.choices[q.answer] : q.answer;
            document.getElementById('outputBody').innerHTML = `
                <div class="answer-banner">
                    <div style="font-size:0.65rem; color:var(--accent);">BONNE RÉPONSE ATTENDUE</div>
                    <div style="font-size:0.9rem;">${correct}</div>
                </div>
                <div class="explanation-block">
                    <div class="ex-text">${data.response}</div>
                </div>
            `;
        });
    }

    function prevQ() { if(currentIndex > 0) { currentIndex--; loadQuestion(currentIndex); } }
    function nextQ() { if(currentIndex < prompts.length - 1) { currentIndex++; loadQuestion(currentIndex); } }
    loadQuestion(0);
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, prompts=PROMPTS, total=len(PROMPTS))

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    model_key = data.get('model', 'fast')
    
    prompt = f"Question : {data.get('question')}\nRéponse étudiant : {data.get('user_code')}\nExplique techniquement et en français la solution."

    # Appel au modèle
    result = call_model(prompt, model_key, choices=None)

    # SAUVEGARDE VERS ELASTICSEARCH
    if es:
        try:
            es.index(index=ELASTIC_INDEX, document={
                "model": model_key,
                "question": data.get('question'),
                "response": result.get("response"),
                "latency": result.get("latency"),
                "timestamp": datetime.datetime.now(datetime.UTC),
                "mode": "web_interface_lab"
            })
        except Exception as e:
            print(f"[-] Erreur indexation : {e}")

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)