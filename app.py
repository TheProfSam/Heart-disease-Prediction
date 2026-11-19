"""CardioSense - Clean 3-Pane Heart Disease Risk Predictor.

Left pane: Home, Mode (White & Blue Light Mode / Dark Mode), History.
Middle pane: Exact 10 input fields, Run Prediction button.
Third pane: Prediction result (High Risk / Low Risk) & Evaluation Metrics.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from prediction_engine import DiagnosticResult, HeartPredictor

# Page Setup
st.set_page_config(
    page_title="Heart Disease Risk Predictor",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light Mode"
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None

# Default Feature Values
defaults = {
    "age": 45,
    "sex": 1,
    "blood_pressure": 120.0,
    "cholesterol": 200.0,
    "bmi": 24.5,
    "smoker": 0,
    "diabetes": 0,
    "physical_activity": 1,
    "family_history": 0,
    "stress_level": 2,
}

for k, v in defaults.items():
    if f"field_{k}" not in st.session_state:
        st.session_state[f"field_{k}"] = v


@st.cache_resource
def load_predictor() -> HeartPredictor:
    return HeartPredictor(Path("heart_disease_rf_model.pkl"))


predictor = load_predictor()


# Theme Styling: White and Blue for Light Mode
def apply_theme(mode: str):
    is_dark = mode == "Dark Mode"
    if is_dark:
        bg = "#0B1120"
        sidebar_bg = "#0F172A"
        card_bg = "#1E293B"
        border = "#334155"
        text = "#F8FAFC"
        subtext = "#94A3B8"
        blue = "#38BDF8"
        box_bg = "#162032"
    else:
        # Crisp White and Blue
        bg = "#FFFFFF"
        sidebar_bg = "#F8FAFC"
        card_bg = "#FFFFFF"
        border = "#BFDBFE"
        text = "#0F172A"
        subtext = "#475569"
        blue = "#1D4ED8"
        box_bg = "#EFF6FF"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg};
            color: {text};
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            border-right: 1px solid {border} !important;
        }}
        [data-testid="stSidebar"] * {{
            color: {text} !important;
        }}
        .pane-card {{
            background-color: {card_bg};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(29, 78, 216, 0.05);
        }}
        .pane-title {{
            font-size: 1.3rem;
            font-weight: 700;
            color: {blue};
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            border-bottom: 2px solid {border};
            padding-bottom: 10px;
        }}
        .status-high {{
            background-color: rgba(239, 68, 68, 0.12);
            border: 2px solid #EF4444;
            color: #DC2626;
            border-radius: 10px;
            padding: 18px;
            text-align: center;
            font-size: 1.5rem;
            font-weight: 800;
            margin-bottom: 24px;
        }}
        .status-low {{
            background-color: rgba(37, 99, 235, 0.1);
            border: 2px solid #2563EB;
            color: #1D4ED8;
            border-radius: 10px;
            padding: 18px;
            text-align: center;
            font-size: 1.5rem;
            font-weight: 800;
            margin-bottom: 24px;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 11px 16px;
            margin-bottom: 8px;
            background: {box_bg};
            border: 1px solid {border};
            border-radius: 8px;
        }}
        .metric-name {{
            font-weight: 600;
            font-size: 0.95rem;
            color: {text};
        }}
        .metric-val {{
            font-weight: 800;
            font-size: 1.15rem;
            color: {blue};
        }}
        div.stButton > button:first-child {{
            background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            width: 100% !important;
            box-shadow: 0 4px 12px rgba(29, 78, 216, 0.25) !important;
        }}
        .history-box {{
            background: {box_bg};
            border-left: 4px solid {blue};
            border-radius: 6px;
            padding: 10px 12px;
            margin-bottom: 10px;
            font-size: 0.85rem;
        }}
        .history-box.high {{
            border-left-color: #EF4444;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# LEFT PANE (SIDEBAR): Home, Mode, History
# ==========================================================
with st.sidebar:
    st.markdown("## 💙 CardioSense")
    st.caption("Heart Disease Risk Prediction System")
    st.write("")

    # 1. HOME BUTTON
    if st.button("🏠 Home / Reset", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[f"field_{k}"] = v
        st.session_state.prediction_result = None
        st.rerun()

    st.write("")
    st.markdown("### ⚙️ Mode")
    theme_choice = st.radio(
        "Select Theme",
        options=["Light Mode", "Dark Mode"],
        index=0 if st.session_state.theme_mode == "Light Mode" else 1,
        help="Switch between White & Blue Light Mode and Dark Mode.",
        label_visibility="collapsed",
    )
    if theme_choice != st.session_state.theme_mode:
        st.session_state.theme_mode = theme_choice
        st.rerun()

    st.write("")
    st.markdown("---")

    # 2. HISTORY
    st.markdown("### 📜 History")
    if not st.session_state.history:
        st.info("No past predictions yet.")
    else:
        for idx, item in enumerate(reversed(st.session_state.history[-6:])):
            is_high = item["result"] == "High Risk"
            cls = "history-box high" if is_high else "history-box"
            st.markdown(
                f"""
                <div class="{cls}">
                    <b>{item['result']}</b> ({item['confidence']}%)<br/>
                    <span style="opacity:0.8; font-size:0.78rem;">{item['timestamp']}</span><br/>
                    <span style="font-size:0.8rem;">Age: {item['inputs']['age']} | BP: {item['inputs']['blood_pressure']} | Chol: {item['inputs']['cholesterol']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()

apply_theme(st.session_state.theme_mode)


# ==========================================================
# MAIN INTERFACE: MIDDLE PANE & THIRD PANE
# ==========================================================
col_middle, col_third = st.columns([1.1, 0.9], gap="large")

# ----------------------------------------------------------
# MIDDLE PANE: Inputting Values (Exact 10 input fields)
# ----------------------------------------------------------
with col_middle:
    st.markdown(
        """
        <div class="pane-card">
            <div class="pane-title">📝 Input Values</div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Age
    age = st.number_input(
        "Age",
        min_value=1,
        max_value=120,
        value=int(st.session_state["field_age"]),
        step=1,
    )
    st.session_state["field_age"] = age

    # 2. Sex
    sex = st.selectbox(
        "Sex",
        options=[("Male", 1), ("Female", 0)],
        index=0 if st.session_state["field_sex"] == 1 else 1,
        format_func=lambda x: x[0],
    )[1]
    st.session_state["field_sex"] = sex

    # 3. Blood Pressure
    blood_pressure = st.number_input(
        "Blood Pressure (mmHg)",
        min_value=50.0,
        max_value=300.0,
        value=float(st.session_state["field_blood_pressure"]),
        step=1.0,
    )
    st.session_state["field_blood_pressure"] = blood_pressure

    # 4. Cholesterol
    cholesterol = st.number_input(
        "Cholesterol (mg/dL)",
        min_value=50.0,
        max_value=600.0,
        value=float(st.session_state["field_cholesterol"]),
        step=1.0,
    )
    st.session_state["field_cholesterol"] = cholesterol

    # 5. BMI
    bmi = st.number_input(
        "BMI",
        min_value=10.0,
        max_value=70.0,
        value=float(st.session_state["field_bmi"]),
        step=0.1,
    )
    st.session_state["field_bmi"] = bmi

    # 6. Smoker
    smoker = st.selectbox(
        "Smoker",
        options=[("No", 0), ("Yes", 1)],
        index=0 if st.session_state["field_smoker"] == 0 else 1,
        format_func=lambda x: x[0],
    )[1]
    st.session_state["field_smoker"] = smoker

    # 7. Diabetes
    diabetes = st.selectbox(
        "Diabetes",
        options=[("No", 0), ("Yes", 1)],
        index=0 if st.session_state["field_diabetes"] == 0 else 1,
        format_func=lambda x: x[0],
    )[1]
    st.session_state["field_diabetes"] = diabetes

    # 8. Physical Activity
    physical_activity = st.selectbox(
        "Physical Activity",
        options=[("No", 0), ("Yes", 1)],
        index=1 if st.session_state["field_physical_activity"] == 1 else 0,
        format_func=lambda x: x[0],
    )[1]
    st.session_state["field_physical_activity"] = physical_activity

    # 9. Family History
    family_history = st.selectbox(
        "Family History",
        options=[("No", 0), ("Yes", 1)],
        index=0 if st.session_state["field_family_history"] == 0 else 1,
        format_func=lambda x: x[0],
    )[1]
    st.session_state["field_family_history"] = family_history

    # 10. Stress Level
    stress_level = st.selectbox(
        "Stress Level",
        options=[(1, "1 (Low)"), (2, "2 (Medium)"), (3, "3 (High)")],
        index=int(st.session_state["field_stress_level"]) - 1,
        format_func=lambda x: x[1],
    )[0]
    st.session_state["field_stress_level"] = stress_level

    st.write("")
    run_btn = st.button("Run Prediction", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# Execute Prediction
if run_btn:
    input_payload = {
        "age": float(age),
        "sex": float(sex),
        "blood_pressure": float(blood_pressure),
        "cholesterol": float(cholesterol),
        "bmi": float(bmi),
        "smoker": float(smoker),
        "diabetes": float(diabetes),
        "physical_activity": float(physical_activity),
        "family_history": float(family_history),
        "stress_level": float(stress_level),
    }

    res = predictor.predict(input_payload)
    st.session_state.prediction_result = res

    # Record in history
    is_high = res.predicted_class == 1
    st.session_state.history.append(
        {
            "timestamp": res.timestamp,
            "result": "High Risk" if is_high else "Low Risk",
            "confidence": round(res.confidence * 100, 1),
            "inputs": {
                "age": int(age),
                "blood_pressure": int(blood_pressure),
                "cholesterol": int(cholesterol),
            },
        }
    )


# ----------------------------------------------------------
# THIRD PANE: Prediction Results & Evaluation Metrics
# ----------------------------------------------------------
with col_third:
    st.markdown(
        """
        <div class="pane-card">
            <div class="pane-title">📊 Prediction Results</div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.prediction_result is None:
        st.info("Input values in the middle pane and click **Run Prediction** to view results.")
    else:
        result: DiagnosticResult = st.session_state.prediction_result
        is_high = result.predicted_class == 1

        # 1. Result stating whether High Risk or Low Risk
        if is_high:
            st.markdown(
                """
                <div class="status-high">
                    ⚠️ High Risk
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="status-low">
                    ✅ Low Risk
                </div>
                """,
                unsafe_allow_html=True,
            )

        # 2. Evaluation Metrics below that
        st.markdown("#### Evaluation Metrics")
        m = result.metrics

        metrics_list = [
            ("Confidence", f"{m.confidence * 100:.1f}%"),
            ("Precision", f"{m.precision * 100:.1f}%"),
            ("Recall", f"{m.recall * 100:.1f}%"),
            ("Specificity", f"{m.specificity * 100:.1f}%"),
            ("F1-Score", f"{m.f1_score * 100:.1f}%"),
            ("Accuracy", f"{m.accuracy * 100:.1f}%"),
            ("ROC-AUC", f"{m.roc_auc:.3f}"),
        ]

        for name, val in metrics_list:
            st.markdown(
                f"""
                <div class="metric-row">
                    <span class="metric-name">{name}</span>
                    <span class="metric-val">{val}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)
