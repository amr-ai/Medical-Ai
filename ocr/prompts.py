# ── Prompts per report type ───────────────────────────────────
PROMPTS = {
    "liver": """You are a medical OCR assistant. Extract liver function test values from this report image.

Return ONLY a valid JSON object with these exact keys (use null if not found):
{
  "age": <number or null>,
  "gender": <1 for Male, 0 for Female, null if not found>,
  "total_bilirubin": <number or null>,
  "alkaline_phosphotase": <number or null>,
  "sgpt_alamine": <number or null>,
  "sgot_aspartate": <number or null>,
  "total_protien": <number or null>,
  "albumin": <number or null>
}
Return ONLY the JSON, no extra text.""",

    "ckd": """You are a medical OCR assistant. Extract kidney function test values from this report image.

Return ONLY a valid JSON object with these exact keys (use null if not found):
{
  "serum_creatinine": <number or null>,
  "blood_urea_nitrogen": <number or null>,
  "albumin_serum": <number or null>,
  "urine_creatinine": <number or null>,
  "urine_albumin": <number or null>,
  "albumin_creatinine_ratio": <number or null>,
  "egfr": <number or null>
}
Return ONLY the JSON, no extra text.""",

    "cbc": """You are a medical OCR assistant. Extract Complete Blood Count (CBC) values from this report image.

Return ONLY a valid JSON object with these exact keys (use null if not found):
{
  "HGB": <number or null>,
  "HCT": <number or null>,
  "RBC": <number or null>,
  "MCV": <number or null>,
  "MCH": <number or null>,
  "MCHC": <number or null>,
  "WBC": <number or null>,
  "PLT": <number or null>
}
Return ONLY the JSON, no extra text.""",
}
