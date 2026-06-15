# MedAI: Advanced Medical Report Analyzer & AI Diagnostic Assistant

MedAI is a sophisticated, AI-powered platform designed to analyze medical laboratory reports, provide predictive insights using machine learning, and offer an interactive AI doctor chat for health-related queries.

## 🚀 Features

- **Automated Report Analysis**: Extracts data from medical reports (PDF/Images) using OCR and Gemini AI.
- **Specialized Diagnostics**:
  - **CBC Analysis**: Full blood count evaluation.
  - **Liver Function**: Assessment of liver enzyme levels and health.
  - **CKD Prediction**: Chronic Kidney Disease risk assessment.
- **AI Doctor Chat**: Interactive consultation powered by OpenRouter (Nemotron) for explaining results and answering health questions.
- **Smart Data Processing**: Automatic unit normalization and null value validation.
- **Visualization**: Graphical representation of lab results and trends.
- **History Tracking**: Keeps a secure log of previous analyses and predictions.

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **AI/ML**: Google Gemini Pro (Vision), Scikit-Learn, Joblib
- **LLM Integration**: OpenRouter API (Nemotron)
- **OCR & Document Processing**: PyMuPDF (fitz), Pillow, OCR techniques
- **Data Science**: Pandas, Matplotlib
- **Reporting**: fpdf2

## 📁 Project Structure

- `/analysis`: Business logic for CBC, CKD, and Liver report processing.
- `/chat`: AI assistant integration logic.
- `/models`: Pre-trained ML models for specific disease predictions.
- `/ocr`: Specialized modules for text and data extraction from documents.
- `/web`: Flask web application (templates, static assets, and app logic).
- `/utils`: Helper functions for unit conversion and data cleaning.

## ⚙️ Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/Medical_Ai.git
   cd Medical_Ai
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Keys**:
   Create a `.env` file in the root directory and add your keys:
   ```env
   GEMINI_API_KEY=your_gemini_key
   OPENROUTER_API_KEY=your_openrouter_key
   FLASK_SECRET_KEY=your_secret_key
   ```

5. **Run the application**:
   ```bash
   python web/app.py
   ```

## 🛡️ Disclaimer

*This application is for educational and informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.*

---
"# Medical-Ai" 
"# Ahmed Metawea"