import joblib
import pandas as pd
from pathlib import Path


# ── Load model artifacts ──────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent / "models" / "CBC"
model    = joblib.load(BASE_DIR / "best_model_cbc.pkl")
scaler   = joblib.load(BASE_DIR / "scaler_cbc.pkl")
encoder  = joblib.load(BASE_DIR / "label_encoder_cbc.pkl")
features = joblib.load(BASE_DIR / "selected_features_cbc.pkl")  # 8 selected features


# ── Prediction ────────────────────────────────────────────────
def predict(data: dict) -> dict:
    """
    data keys (match OCR output or manual input):
      HGB, HCT, RBC, MCV, MCH, MCHC, WBC, PLT
    """
    # Normalize units
    if data.get("WBC", 0) > 100:
        data["WBC"] = data["WBC"] / 1000.0
    if data.get("PLT", 0) > 10000:
        data["PLT"] = data["PLT"] / 1000.0

    patient = pd.DataFrame([data])[features]
    scaled  = scaler.transform(patient)

    pred    = model.predict(scaled)
    proba   = model.predict_proba(scaled)

    label      = encoder.inverse_transform(pred)[0]
    confidence_val = proba.max()
    confidence = f"{confidence_val:.2%}"

    return {
        "result": label, 
        "confidence": confidence,
        "low_confidence": bool(confidence_val < 0.60)
    }


# ── Print result ──────────────────────────────────────────────
def print_result(result: dict):
    print("=" * 45)
    print("      COMPLETE BLOOD COUNT (CBC) RESULT")
    print("=" * 45)
    print(f"  Prediction : {result['result']}")
    print(f"  Confidence : {result['confidence']}")
    print("=" * 45)
    
    if result.get("low_confidence"):
        print("  ⚠️  Low confidence prediction — please consult a doctor for verification.")
        
    label_lower = result["result"].lower()
    if "normal" in label_lower or "healthy" in label_lower:
        print("  ✅  CBC values appear normal.")
    elif "anemia" in label_lower:
        print("  ⚠️  Signs of anemia detected — consult a doctor.")
    else:
        print(f"  ⚠️  Condition detected: {result['result']} — consult a doctor.")
