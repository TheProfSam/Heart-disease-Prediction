# CardioSense — Clean 3-Pane Heart Disease Risk Predictor

A streamlined, clean Python web application built with **Streamlit** for heart disease risk prediction.

---

## 3-Pane Interface Architecture

### 1. Left Pane (Sidebar)
- **Home / Reset**: One-click reset to default baseline values and home state.
- **Mode**: Toggle between **Light Mode** (Crisp Medical White & Blue) and **Dark Mode**.
- **History**: Keeps track of previous assessments (prediction result, confidence, timestamp, inputs) with a **Clear History** button.

### 2. Middle Pane (Input Values)
The exact 10 clinical input fields matching the trained Random Forest model:
1. **Age**
2. **Sex** (Male / Female)
3. **Blood Pressure (mmHg)**
4. **Cholesterol (mg/dL)**
5. **BMI**
6. **Smoker** (No / Yes)
7. **Diabetes** (No / Yes)
8. **Physical Activity** (No / Yes)
9. **Family History** (No / Yes)
10. **Stress Level** (1 - Low, 2 - Medium, 3 - High)
- **Run Prediction Button**: Full-width button to execute the prediction.

### 3. Third Pane (Prediction Results)
- **Prediction Result**: Clean, prominent status badge stating **High Risk** or **Low Risk**.
- **Evaluation Metrics** (displayed cleanly below the result):
  - **Confidence** (%)
  - **Precision** (%)
  - **Recall** (%)
  - **Specificity** (%)
  - **F1-Score** (%)
  - **Accuracy** (%)
  - **ROC-AUC**

---

## How to Run

### Command:
```powershell
streamlit run app.py
```
Or double-click `run_web_app.bat`.

The app runs on:
`http://localhost:8501`
