import joblib
import pandas as pd
from pathlib import Path

# ── Load model artifacts ──────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent / "models" / "CKD"
model  = joblib.load(BASE_DIR / "CKD_model.pkl")
scaler = joblib.load(BASE_DIR / "CKD_scaler.pkl")

FEATURE_NAMES = [
    "serum_creatinine",
    "blood_urea_nitrogen",
    "albumin_serum",
    "urine_creatinine",
    "urine_albumin",
    "albumin_creatinine_ratio",
    "egfr",
]


# ── Prediction ────────────────────────────────────────────────
def predict(data: dict) -> dict:
    """
    data keys (match OCR output or manual input):
      serum_creatinine, blood_urea_nitrogen, albumin_serum,
      urine_creatinine, urine_albumin, albumin_creatinine_ratio, egfr
    """
    patient    = pd.DataFrame([data], columns=FEATURE_NAMES)
    scaled     = scaler.transform(patient)

    prediction = model.predict(scaled)[0]
    proba      = model.predict_proba(scaled)[0]

    # Build per-class confidence string
    class_probs = {
        f"Stage {stage}": f"{prob * 100:.1f}%"
        for stage, prob in zip(model.classes_, proba)
    }
    
    confidence_val = max(proba)

    return {
        "result":       f"CKD Stage {prediction}",
        "confidence":   f"{confidence_val * 100:.1f}%",
        "class_probs":  class_probs,
        "low_confidence": bool(confidence_val < 0.60)
    }


# ── Print result ──────────────────────────────────────────────
def print_result(result: dict):
    print("=" * 45)
    print("       KIDNEY FUNCTION TEST RESULT")
    print("=" * 45)
    print(f"  Predicted Stage : {result['result']}")
    print(f"  Confidence      : {result['confidence']}")
    print("\n  Confidence per stage:")
    for stage, prob in result["class_probs"].items():
        print(f"    {stage}: {prob}")
    print("=" * 45)
    
    if result.get("low_confidence"):
        print("  ⚠️  Low confidence prediction — please consult a doctor for verification.")
        
    stage_num = int(result["result"].split("Stage")[-1].strip())
    if stage_num == 0:
        print("  ✅  Kidney function appears healthy.")
    elif stage_num <= 2:
        print("  🟡  Early-stage CKD — monitor and consult a doctor.")
    elif stage_num <= 4:
        print("  🟠  Moderate CKD — medical attention recommended.")
    else:
        print("  🔴  Severe CKD — urgent medical care needed.")
