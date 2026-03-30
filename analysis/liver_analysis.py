import joblib
import pandas as pd
from pathlib import Path


# ── Load model artifacts ──────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent / "models" / "Liver"
model        = joblib.load(BASE_DIR / "liver_model.pkl")
scaler       = joblib.load(BASE_DIR / "robust_scaler.pkl")
feature_names = joblib.load(BASE_DIR / "feature_names.pkl")


# ── Prediction ────────────────────────────────────────────────
def predict(data: dict) -> dict:
    """
    data keys (match OCR output or manual input):
      age, gender, total_bilirubin, alkaline_phosphotase,
      sgpt_alamine, sgot_aspartate, total_protien, albumin
    """
    patient = pd.DataFrame([{
        "Age of the patient":              data["age"],
        "Gender of the patient":           data["gender"],
        "Total Bilirubin":                 data["total_bilirubin"],
        "Alkphos Alkaline Phosphotase":    data["alkaline_phosphotase"],
        "Sgpt Alamine Aminotransferase":   data["sgpt_alamine"],
        "Sgot Aspartate Aminotransferase": data["sgot_aspartate"],
        "Total Protiens":                  data["total_protien"],
        "ALB Albumin":                     data["albumin"],
    }])

    # Keep column order consistent with training
    patient        = patient[feature_names]
    scaled         = scaler.transform(patient)
    scaled_df      = pd.DataFrame(scaled, columns=patient.columns)

    prediction     = model.predict(scaled_df)[0]
    proba          = model.predict_proba(scaled_df)[0].tolist()

    label          = "Liver Disease" if prediction == 1 else "Healthy"
    confidence_val = max(proba)
    confidence     = f"{confidence_val * 100:.1f}%"

    return {
        "result": label, 
        "confidence": confidence,
        "low_confidence": bool(confidence_val < 0.60)
    }


# ── Print result ──────────────────────────────────────────────
def print_result(result: dict):
    print("=" * 45)
    print("        LIVER FUNCTION TEST RESULT")
    print("=" * 45)
    print(f"  Prediction : {result['result']}")
    print(f"  Confidence : {result['confidence']}")
    print("=" * 45)
    
    if result.get("low_confidence"):
        print("  ⚠️  Low confidence prediction — please consult a doctor for verification.")
        
    if result["result"] == "Liver Disease":
        print("  ⚠️  Patient may have liver disease — consult a doctor.")
    else:
        print("  ✅  Patient appears healthy.")
