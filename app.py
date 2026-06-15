import os
import sys
import json
from datetime import datetime
from flask import Flask, request, render_template, jsonify, session, send_file, redirect, url_for
from werkzeug.utils import secure_filename

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr.extractor import detect_report_type, detect_type_from_text, run_ocr, get_first_page_image
from analysis import cbc_analysis, liver_analysis, ckd_analysis
from utils.range_checker import check_ranges
from utils.pdf_exporter import export_pdf
from utils.trend_chart import plot_trends
from chat.doctor_chat import get_reply, get_assistant_reply

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(current_dir, "templates"),
            static_folder=os.path.join(current_dir, "static"))
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

HISTORY_FILE = "history.json"

REPORT_MODULES = {
    "cbc": cbc_analysis,
    "ckd": ckd_analysis,
    "liver": liver_analysis
}

MANUAL_FIELDS = {
    "liver": [
        ("age", "Age"),
        ("gender", "Gender (1=Male, 0=Female)"),
        ("total_bilirubin", "Total Bilirubin"),
        ("alkaline_phosphotase", "Alkaline Phosphotase"),
        ("sgpt_alamine", "SGPT / Alamine Aminotransferase"),
        ("sgot_aspartate", "SGOT / Aspartate Aminotransferase"),
        ("total_protien", "Total Protein"),
        ("albumin", "Albumin"),
    ],
    "ckd": [
        ("serum_creatinine", "Serum Creatinine"),
        ("blood_urea_nitrogen", "Blood Urea Nitrogen (BUN)"),
        ("albumin_serum", "Albumin (Serum)"),
        ("urine_creatinine", "Urine Creatinine"),
        ("urine_albumin", "Urine Albumin"),
        ("albumin_creatinine_ratio", "Albumin-to-Creatinine Ratio (ACR)"),
        ("egfr", "eGFR"),
    ],
    "cbc": [
        ("HGB", "Hemoglobin (HGB)"),
        ("HCT", "Hematocrit (HCT)"),
        ("RBC", "Red Blood Cells (RBC)"),
        ("MCV", "MCV"),
        ("MCH", "MCH"),
        ("MCHC", "MCHC"),
        ("WBC", "White Blood Cells (WBC)"),
        ("PLT", "Platelets (PLT)"),
    ],
}

def save_history(entry):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            pass
    history.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", all_fields=MANUAL_FIELDS)

@app.route("/analyze", methods=["POST"])
def analyze():
    patient_name = request.form.get("patient_name")
    patient_id = request.form.get("patient_id")
    input_method = request.form.get("input_method")
    
    is_manual_completion = request.form.get("is_manual_completion") == "true"
    
    if is_manual_completion:
        report_type = request.form.get("report_type")
        data = {}
        partial_data = json.loads(request.form.get("partial_data", "{}"))
        data.update(partial_data)
        
        for key, _ in MANUAL_FIELDS[report_type]:
            val = request.form.get(key)
            if val:
                try:
                    data[key] = float(val)
                except ValueError:
                    pass
    elif input_method == "manual":
        report_type = request.form.get("report_type")
        if report_type not in MANUAL_FIELDS:
            return "Invalid report type", 400

        data = {}
        for key, _ in MANUAL_FIELDS[report_type]:
            val = request.form.get(key)
            if val is None or str(val).strip() == "":
                data[key] = None
                continue

            # gender is encoded as 1/0 in the downstream model
            if report_type == "liver" and key == "gender":
                try:
                    data[key] = float(int(val))
                except ValueError:
                    data[key] = None
                continue

            try:
                data[key] = float(val)
            except ValueError:
                data[key] = None
    elif input_method == "upload":
        if "file" not in request.files or request.files["file"].filename == "":
            return "No file uploaded", 400
            
        file = request.files["file"]
        os.makedirs("results", exist_ok=True)
        safe_name = secure_filename(file.filename) or "upload"
        temp_path = os.path.abspath(os.path.join("results", safe_name))
        file.save(temp_path)
        
        try:
            img_bytes = get_first_page_image(temp_path)
            report_type = detect_report_type(img_bytes)
            data = run_ocr(temp_path, report_type)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        missing = [k for k, v in data.items() if v is None]
        if missing:
            return render_template(
                "index.html", patient_name=patient_name, patient_id=patient_id, 
                report_type=report_type, missing_fields=missing, 
                partial_data=json.dumps(data), all_fields=MANUAL_FIELDS
            )
    else:
        return "Invalid input method", 400

    abnormal_fields = check_ranges(report_type, data)
    
    module = REPORT_MODULES[report_type]
    data_for_pred = dict(data)  # Copy for predict since it can mutate
    result = module.predict(data_for_pred)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "patient_name": patient_name,
        "patient_id": patient_id,
        "report_type": report_type,
        "extracted_values": data,
        "prediction_result": result
    }
    save_history(entry)
    
    session["report_data"] = {
        "patient_name": patient_name,
        "patient_id": patient_id,
        "report_type": report_type,
        "extracted_values": data,
        "prediction_result": result,
        "abnormal_fields": abnormal_fields
    }
    
    return render_template("result.html", data=session["report_data"])

@app.route("/chat", methods=["POST"])
def chat():
    req = request.json
    msg = req.get("message")
    history = req.get("history", [])
    
    report_data = session.get("report_data")
    if not report_data:
        return jsonify({"reply": "Session expired."})
        
    history.append({"role": "user", "content": msg})
    
    reply = get_reply(
        report_data["report_type"],
        report_data["extracted_values"],
        report_data["prediction_result"],
        history
    )
    
    return jsonify({"reply": reply})


@app.route("/assistant", methods=["GET"])
def assistant():
    return render_template("assistant_chat.html")


@app.route("/chat_assistant", methods=["POST"])
def chat_assistant():
    req = request.json or {}
    msg = (req.get("message") or "").strip()
    history = req.get("history", [])

    if not msg:
        return jsonify({"reply": "Please type a question."})

    reply = get_assistant_reply(msg, history)
    return jsonify({"reply": reply})

@app.route("/export", methods=["POST"])
def export():
    report_data = session.get("report_data")
    if not report_data:
        return "Session expired", 400
        
    pdf_path = export_pdf(
        report_data["patient_name"],
        report_data["patient_id"],
        report_data["report_type"],
        report_data["extracted_values"],
        report_data["prediction_result"],
        report_data["abnormal_fields"]
    )
    
    return send_file(os.path.abspath(pdf_path), as_attachment=True)

@app.route("/history", methods=["GET"])
def history_view():
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                pass
    
    patients = {}
    stats = {"total": 0, "cbc": 0, "ckd": 0, "liver": 0}
    for r in history:
        pid = r.get("patient_id")
        if pid not in patients:
            patients[pid] = []
        patients[pid].append(r)

        stats["total"] += 1
        rt = (r.get("report_type") or "").lower()
        if rt in ("cbc", "ckd", "liver"):
            stats[rt] += 1
        
    return render_template("history.html", patients=patients, stats=stats)

@app.route("/trends/<patient_id>/<report_type>")
def trends(patient_id, report_type):
    path = plot_trends(patient_id, report_type)
    if not path:
        return jsonify({"error": "Not enough data"})
    return send_file(os.path.abspath(path), mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True, port=5000)
