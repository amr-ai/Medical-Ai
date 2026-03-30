import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

def plot_trends(patient_id: str, report_type: str):
    history_file = "history.json"
    if not os.path.exists(history_file):
        return None
        
    try:
        with open(history_file, "r") as f:
            history = json.load(f)
    except Exception:
        return None
        
    patient_records = [
        r for r in history 
        if str(r.get("patient_id")) == str(patient_id) and r.get("report_type") == report_type
    ]
    
    # Sort chronologically
    patient_records.sort(key=lambda x: x.get("timestamp", ""))
    
    if len(patient_records) < 2:
        return None # Require at least 2 points to trend
        
    metrics = []
    if report_type == "cbc":
        metrics = ["HGB", "WBC", "PLT"]
    elif report_type == "ckd":
        metrics = ["serum_creatinine", "egfr"]
    elif report_type == "liver":
        metrics = ["total_bilirubin", "sgpt_alamine", "sgot_aspartate"]
        
    if not metrics:
        return None
        
    os.makedirs("results", exist_ok=True)
    filename = f"results/trend_{patient_id}_{report_type}.png"
    
    dates = []
    values = {m: [] for m in metrics}
    
    for r in patient_records:
        dt_str = r.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(dt_str)
            dt_formatted = dt.strftime("%m/%d" if dt.year == datetime.now().year else "%m/%y")
        except:
            dt_formatted = dt_str[:10]
            
        dates.append(dt_formatted)
        
        ext = r.get("extracted_values", {})
        for m in metrics:
            val = ext.get(m, 0)
            if val is None:
                val = 0
            values[m].append(float(val))
            
    plt.figure(figsize=(10, 6))
    for m in metrics:
        plt.plot(dates, values[m], marker='o', label=m)
        
    plt.title(f"{report_type.upper()} Trends for Patient {patient_id}")
    plt.xlabel("Timeline")
    plt.ylabel("Value")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    
    return filename
