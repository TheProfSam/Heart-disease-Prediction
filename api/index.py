"""Vercel Serverless Entrypoint for CardioSense Heart Disease Predictor.

Provides a native web interface and prediction API for Vercel deployment.
Includes the exact 3-pane layout:
- Left pane: Home, Mode (White & Blue Light Mode / Dark Mode), History
- Middle pane: Exact 10 clinical input fields with Run Prediction button
- Third pane: Prediction outcome (High Risk / Low Risk) & Evaluation Metrics
"""

import sys
from pathlib import Path

# Add project root to path for imports
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from flask import Flask, jsonify, render_template_string, request
from prediction_engine import HeartPredictor

app = Flask(__name__)
predictor = HeartPredictor()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CardioSense - Heart Disease Risk Predictor</title>
  <style>
    :root {
      --bg: #FFFFFF;
      --sidebar-bg: #F8FAFC;
      --card-bg: #FFFFFF;
      --border: #BFDBFE;
      --text: #0F172A;
      --subtext: #475569;
      --blue: #1D4ED8;
      --box-bg: #EFF6FF;
      --input-bg: #FFFFFF;
      --input-border: #CBD5E1;
      --shadow: 0 4px 16px rgba(29, 78, 216, 0.05);
    }

    [data-theme="dark"] {
      --bg: #0B1120;
      --sidebar-bg: #0F172A;
      --card-bg: #1E293B;
      --border: #334155;
      --text: #F8FAFC;
      --subtext: #94A3B8;
      --blue: #38BDF8;
      --box-bg: #162032;
      --input-bg: #0F172A;
      --input-border: #475569;
      --shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      display: flex;
      min-height: 100vh;
      transition: background-color 0.2s, color 0.2s;
    }

    /* Left Pane (Sidebar) */
    .sidebar {
      width: 280px;
      background: var(--sidebar-bg);
      border-right: 1px solid var(--border);
      padding: 24px 18px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      flex-shrink: 0;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 1.35rem;
      font-weight: 800;
      color: var(--blue);
    }
    .brand-sub {
      font-size: 0.8rem;
      color: var(--subtext);
      margin-top: 2px;
    }

    .btn-home {
      width: 100%;
      padding: 10px 14px;
      background: var(--box-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s;
    }
    .btn-home:hover {
      border-color: var(--blue);
      color: var(--blue);
    }

    .section-title {
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-weight: 700;
      color: var(--subtext);
      margin-bottom: 8px;
    }

    .theme-toggle {
      display: flex;
      background: var(--box-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 3px;
      gap: 4px;
    }
    .theme-btn {
      flex: 1;
      padding: 8px;
      border: none;
      background: transparent;
      color: var(--subtext);
      font-size: 0.85rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .theme-btn.active {
      background: var(--card-bg);
      color: var(--blue);
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }

    .history-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      overflow-y: auto;
      max-height: 380px;
    }
    .history-item {
      background: var(--box-bg);
      border-left: 4px solid var(--blue);
      border-radius: 6px;
      padding: 10px 12px;
      font-size: 0.82rem;
    }
    .history-item.high {
      border-left-color: #EF4444;
    }
    .history-item-title {
      font-weight: 700;
      display: flex;
      justify-content: space-between;
    }
    .history-meta {
      font-size: 0.74rem;
      color: var(--subtext);
      margin-top: 4px;
    }
    .btn-clear {
      width: 100%;
      padding: 8px;
      background: transparent;
      border: 1px dashed var(--border);
      border-radius: 6px;
      color: var(--subtext);
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-clear:hover {
      border-color: #EF4444;
      color: #EF4444;
    }

    /* Main Area: Middle & Third Panes */
    .main-content {
      flex: 1;
      padding: 32px 36px;
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 28px;
      max-width: 1350px;
    }

    .pane-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
    }

    .pane-header {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--blue);
      padding-bottom: 12px;
      margin-bottom: 18px;
      border-bottom: 2px solid var(--border);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* Form Fields Grid */
    .fields-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .form-group label {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text);
    }
    .form-control {
      padding: 9px 12px;
      background: var(--input-bg);
      border: 1px solid var(--input-border);
      border-radius: 7px;
      color: var(--text);
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s;
    }
    .form-control:focus {
      border-color: var(--blue);
    }

    .btn-predict {
      margin-top: 24px;
      padding: 13px;
      background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%);
      color: #FFFFFF;
      font-size: 1rem;
      font-weight: 700;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(29, 78, 216, 0.25);
      transition: transform 0.15s, box-shadow 0.15s;
    }
    .btn-predict:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(29, 78, 216, 0.35);
    }

    /* Results Pane */
    .status-badge {
      padding: 18px;
      border-radius: 10px;
      text-align: center;
      font-size: 1.45rem;
      font-weight: 800;
      margin-bottom: 22px;
    }
    .status-badge.high {
      background: rgba(239, 68, 68, 0.12);
      border: 2px solid #EF4444;
      color: #DC2626;
    }
    .status-badge.low {
      background: rgba(37, 99, 235, 0.1);
      border: 2px solid #2563EB;
      color: #1D4ED8;
    }

    .metrics-title {
      font-size: 1rem;
      font-weight: 700;
      margin-bottom: 14px;
      color: var(--text);
    }
    .metrics-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .metric-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      background: var(--box-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
    }
    .metric-name {
      font-size: 0.92rem;
      font-weight: 600;
    }
    .metric-val {
      font-size: 1.15rem;
      font-weight: 800;
      color: var(--blue);
    }

    .placeholder-msg {
      color: var(--subtext);
      font-size: 0.95rem;
      padding: 24px;
      text-align: center;
      background: var(--box-bg);
      border: 1px dashed var(--border);
      border-radius: 8px;
      margin: auto 0;
    }

    @media (max-width: 900px) {
      body { flex-direction: column; }
      .sidebar { width: 100%; border-right: none; border-bottom: 1px solid var(--border); }
      .main-content { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <!-- LEFT PANE -->
  <aside class="sidebar">
    <div>
      <div class="brand"><span>💙</span> CardioSense</div>
      <div class="brand-sub">Heart Disease Risk Predictor</div>
    </div>

    <button class="btn-home" onclick="resetForm()">🏠 Home / Reset</button>

    <div>
      <div class="section-title">Mode</div>
      <div class="theme-toggle">
        <button id="btnLight" class="theme-btn active" onclick="setTheme('light')">Light Mode</button>
        <button id="btnDark" class="theme-btn" onclick="setTheme('dark')">Dark Mode</button>
      </div>
    </div>

    <div style="flex:1; display:flex; flex-direction:column; min-height:0;">
      <div class="section-title" style="display:flex; justify-content:space-between; align-items:center;">
        <span>📜 History</span>
        <button class="btn-clear" style="width:auto; padding:2px 6px;" onclick="clearHistory()">Clear</button>
      </div>
      <div class="history-list" id="historyList">
        <div style="font-size:0.8rem; color:var(--subtext); padding:8px;">No past predictions yet.</div>
      </div>
    </div>
  </aside>

  <!-- MAIN AREA: MIDDLE PANE & THIRD PANE -->
  <main class="main-content">
    <!-- MIDDLE PANE: Inputting Values -->
    <section class="pane-card">
      <div class="pane-header">📝 Input Values</div>

      <div class="fields-grid">
        <div class="form-group">
          <label for="age">Age</label>
          <input type="number" id="age" class="form-control" value="45" min="1" max="120">
        </div>

        <div class="form-group">
          <label for="sex">Sex</label>
          <select id="sex" class="form-control">
            <option value="1" selected>Male</option>
            <option value="0">Female</option>
          </select>
        </div>

        <div class="form-group">
          <label for="blood_pressure">Blood Pressure (mmHg)</label>
          <input type="number" id="blood_pressure" class="form-control" value="120" min="50" max="300">
        </div>

        <div class="form-group">
          <label for="cholesterol">Cholesterol (mg/dL)</label>
          <input type="number" id="cholesterol" class="form-control" value="200" min="50" max="600">
        </div>

        <div class="form-group">
          <label for="bmi">BMI</label>
          <input type="number" id="bmi" class="form-control" value="24.5" step="0.1" min="10" max="70">
        </div>

        <div class="form-group">
          <label for="smoker">Smoker</label>
          <select id="smoker" class="form-control">
            <option value="0" selected>No</option>
            <option value="1">Yes</option>
          </select>
        </div>

        <div class="form-group">
          <label for="diabetes">Diabetes</label>
          <select id="diabetes" class="form-control">
            <option value="0" selected>No</option>
            <option value="1">Yes</option>
          </select>
        </div>

        <div class="form-group">
          <label for="physical_activity">Physical Activity</label>
          <select id="physical_activity" class="form-control">
            <option value="1" selected>Yes</option>
            <option value="0">No</option>
          </select>
        </div>

        <div class="form-group">
          <label for="family_history">Family History</label>
          <select id="family_history" class="form-control">
            <option value="0" selected>No</option>
            <option value="1">Yes</option>
          </select>
        </div>

        <div class="form-group">
          <label for="stress_level">Stress Level</label>
          <select id="stress_level" class="form-control">
            <option value="1">1 (Low)</option>
            <option value="2" selected>2 (Medium)</option>
            <option value="3">3 (High)</option>
          </select>
        </div>
      </div>

      <button class="btn-predict" onclick="runPrediction()">Run Prediction</button>
    </section>

    <!-- THIRD PANE: Prediction Results -->
    <section class="pane-card">
      <div class="pane-header">📊 Prediction Results</div>

      <div id="resultsContent" style="display:flex; flex-direction:column; height:100%;">
        <div class="placeholder-msg">
          Input values in the middle pane and click <b>Run Prediction</b> to view results.
        </div>
      </div>
    </section>
  </main>

  <script>
    // Theme toggle
    function setTheme(theme) {
      if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.getElementById('btnDark').classList.add('active');
        document.getElementById('btnLight').classList.remove('active');
      } else {
        document.documentElement.removeAttribute('data-theme');
        document.getElementById('btnLight').classList.add('active');
        document.getElementById('btnDark').classList.remove('active');
      }
      localStorage.setItem('cardiosense_theme', theme);
    }

    const savedTheme = localStorage.getItem('cardiosense_theme');
    if (savedTheme) setTheme(savedTheme);

    // Form Reset
    function resetForm() {
      document.getElementById('age').value = '45';
      document.getElementById('sex').value = '1';
      document.getElementById('blood_pressure').value = '120';
      document.getElementById('cholesterol').value = '200';
      document.getElementById('bmi').value = '24.5';
      document.getElementById('smoker').value = '0';
      document.getElementById('diabetes').value = '0';
      document.getElementById('physical_activity').value = '1';
      document.getElementById('family_history').value = '0';
      document.getElementById('stress_level').value = '2';

      document.getElementById('resultsContent').innerHTML = `
        <div class="placeholder-msg">
          Input values in the middle pane and click <b>Run Prediction</b> to view results.
        </div>
      `;
    }

    // Prediction Execution
    async function runPrediction() {
      const payload = {
        age: parseFloat(document.getElementById('age').value),
        sex: parseFloat(document.getElementById('sex').value),
        blood_pressure: parseFloat(document.getElementById('blood_pressure').value),
        cholesterol: parseFloat(document.getElementById('cholesterol').value),
        bmi: parseFloat(document.getElementById('bmi').value),
        smoker: parseFloat(document.getElementById('smoker').value),
        diabetes: parseFloat(document.getElementById('diabetes').value),
        physical_activity: parseFloat(document.getElementById('physical_activity').value),
        family_history: parseFloat(document.getElementById('family_history').value),
        stress_level: parseFloat(document.getElementById('stress_level').value),
      };

      try {
        const resp = await fetch('/api/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await resp.json();

        // Render Results
        const isHigh = data.predicted_class === 1;
        const badgeClass = isHigh ? 'status-badge high' : 'status-badge low';
        const badgeText = isHigh ? '⚠️ High Risk' : '✅ Low Risk';

        const metricsHtml = `
          <div class="${badgeClass}">${badgeText}</div>
          <div class="metrics-title">Evaluation Metrics</div>
          <div class="metrics-list">
            <div class="metric-row"><span class="metric-name">Confidence</span><span class="metric-val">${data.metrics.Confidence}%</span></div>
            <div class="metric-row"><span class="metric-name">Precision</span><span class="metric-val">${data.metrics.Precision}%</span></div>
            <div class="metric-row"><span class="metric-name">Recall</span><span class="metric-val">${data.metrics['Recall (Sensitivity)']}%</span></div>
            <div class="metric-row"><span class="metric-name">Specificity</span><span class="metric-val">${data.metrics.Specificity}%</span></div>
            <div class="metric-row"><span class="metric-name">F1-Score</span><span class="metric-val">${data.metrics['F1-Score']}%</span></div>
            <div class="metric-row"><span class="metric-name">Accuracy</span><span class="metric-val">${data.metrics['Model Accuracy']}%</span></div>
            <div class="metric-row"><span class="metric-name">ROC-AUC</span><span class="metric-val">${data.metrics['ROC-AUC']}</span></div>
          </div>
        `;
        document.getElementById('resultsContent').innerHTML = metricsHtml;

        // Save to History
        saveHistory({
          result: isHigh ? 'High Risk' : 'Low Risk',
          confidence: data.metrics.Confidence,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          age: payload.age,
          bp: payload.blood_pressure,
          chol: payload.cholesterol,
          isHigh: isHigh
        });
      } catch (err) {
        alert('Prediction error: ' + err.message);
      }
    }

    // History Storage
    function getHistory() {
      try { return JSON.parse(localStorage.getItem('cardiosense_hist') || '[]'); } catch { return []; }
    }
    function saveHistory(item) {
      const hist = getHistory();
      hist.unshift(item);
      if (hist.length > 8) hist.pop();
      localStorage.setItem('cardiosense_hist', JSON.stringify(hist));
      renderHistory();
    }
    function clearHistory() {
      localStorage.removeItem('cardiosense_hist');
      renderHistory();
    }
    function renderHistory() {
      const hist = getHistory();
      const el = document.getElementById('historyList');
      if (hist.length === 0) {
        el.innerHTML = '<div style="font-size:0.8rem; color:var(--subtext); padding:8px;">No past predictions yet.</div>';
        return;
      }
      el.innerHTML = hist.map(h => `
        <div class="history-item ${h.isHigh ? 'high' : ''}">
          <div class="history-item-title">
            <span>${h.result}</span>
            <span>${h.confidence}%</span>
          </div>
          <div class="history-meta">${h.timestamp} • Age: ${h.age} | BP: ${h.bp} | Chol: ${h.chol}</div>
        </div>
      `).join('');
    }

    renderHistory();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True) or {}
        res = predictor.predict(data)
        return jsonify({
            "predicted_class": res.predicted_class,
            "predicted_label": res.predicted_label,
            "confidence": round(res.confidence * 100, 2),
            "metrics": res.metrics.to_dict(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
