from fpdf import FPDF
import os
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'MedAI - Medical Lab Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'This report is AI-generated. Always consult a licensed doctor.', 0, 0, 'C')

def export_pdf(patient_name: str, patient_id: str, report_type: str, 
               extracted_values: dict, prediction_result: dict, abnormal_fields: list) -> str:
    
    os.makedirs("results", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"results/report_{report_type}_{timestamp}.pdf"
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
    pdf.cell(200, 10, txt=f"Patient Name: {patient_name}", ln=1)
    pdf.cell(200, 10, txt=f"Patient ID: {patient_id}", ln=1)
    pdf.cell(200, 10, txt=f"Report Type: {report_type.upper()}", ln=1)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Extracted Values & Normal Ranges", ln=1)
    
    pdf.set_font("Arial", size=12)
    abnormal_keys = [a["field"] for a in abnormal_fields]
    
    for k, v in extracted_values.items():
        if k in abnormal_keys:
            pdf.set_text_color(220, 53, 69) # Red
            flag = "[ABNORMAL] "
        else:
            pdf.set_text_color(0, 0, 0)
            flag = ""
            
        pdf.cell(200, 10, txt=f"{flag}{k}: {v}", ln=1)
        
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="AI Prediction Result", ln=1)
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt=f"Result: {prediction_result.get('result', '')}", ln=1)
    pdf.cell(200, 10, txt=f"Confidence: {prediction_result.get('confidence', 'N/A')}", ln=1)
    if prediction_result.get('low_confidence'):
        pdf.cell(200, 10, txt="Note: Low confidence prediction. Consult doctor immediately.", ln=1)
    
    # Needs latin-1 compatible chars. FPDF simple usage won't handle emojis safely etc.
    pdf.output(filename)
    return filename
