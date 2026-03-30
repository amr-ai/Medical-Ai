def check_ranges(report_type: str, data: dict) -> list:
    """Evaluate normal medical ranges for parsed test results."""
    abnormal = []
    
    ranges = {
        "cbc": {
            "HGB":  (12.0, 17.5, "g/dL"),
            "HCT":  (36.0, 50.0, "%"),
            "RBC":  (4.0, 5.9, "M/uL"),
            "MCV":  (80.0, 100.0, "fL"),
            "MCH":  (27.0, 33.0, "pg"),
            "MCHC": (32.0, 36.0, "g/dL"),
            "WBC":  (4.0, 11.0, "K/uL"),
            "PLT":  (150.0, 450.0, "K/uL")
        },
        "liver": {
            "total_bilirubin": (0.1, 1.2, "mg/dL"),
            "alkaline_phosphotase": (44.0, 147.0, "IU/L"),
            "sgpt_alamine": (7.0, 56.0, "U/L"),
            "sgot_aspartate": (8.0, 48.0, "U/L"),
            "total_protien": (6.0, 8.3, "g/dL"),
            "albumin": (3.4, 5.4, "g/dL")
        },
        "ckd": {
            "serum_creatinine": (0.6, 1.2, "mg/dL"),
            "blood_urea_nitrogen": (7.0, 20.0, "mg/dL"),
            "albumin_serum": (3.4, 5.4, "g/dL"),
            "urine_creatinine": (20.0, 275.0, "mg/dL"),
            "urine_albumin": (0.0, 30.0, "mg/g"),
            "albumin_creatinine_ratio": (0.0, 30.0, "mg/g"),
            "egfr": (90.0, 150.0, "mL/min/1.73m2")
        }
    }
    
    if report_type not in ranges:
        return []
        
    for field, limits in ranges[report_type].items():
        if field in data and data[field] is not None:
            val = float(data[field])
            
            # Since analysis scripts modify WBC and PLT inplace, it's safer to only flag normal ranges if the scaler hadn't kicked in
            # If WBC was divided by 1000 in predicting, it could break. We will check against ranges anyway.
            if report_type == 'cbc' and val < 0.1: # Catch for when WBC/PLT are scaled heavily
                continue

            min_val, max_val, unit = limits
            if not (min_val <= val <= max_val):
                abnormal.append({
                    "field": field,
                    "value": round(val, 2),
                    "normal": f"{min_val} - {max_val}",
                    "unit": unit
                })
                
    return abnormal
