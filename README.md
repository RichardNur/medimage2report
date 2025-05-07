# 🧠 Medical Report Generation from Image Analysis Outputs  
### Transform PDF-Based Medical Image Evaluations into Structured Radiology Reports


## 📌 Problem

Radiologists increasingly rely on image analysis tools and AI algorithms to support diagnostic interpretation of imaging studies (e.g., brain volumetry, lesion detection, PET/CT analyses). However, these systems often output results in **PDF** or **DICOM** format, requiring manual review and integration into radiology reports.

This manual process is **time-consuming**, **error-prone**, and contributes to reporting fatigue—particularly in high-throughput environments.


## 💡 Solution

This project introduces a **modular backend system** that receives PDF outputs from medical image analysis applications, extracts relevant findings, and automatically generates **RSNA-compliant structured radiology report text** using the **OpenAI GPT API**.

It is designed to assist radiologists by:
- Reducing the time spent manually converting AI outputs into text,
- Promoting consistency in language and formatting,
- Ensuring findings are clinically actionable and well-structured.

### 🔄 Workflow Overview

1. **PDF Upload**  
   The user uploads an Analysis-PDF (e.g., brain volumetry or PET/CT analysis).

2. **Anonymization & Extraction**  
   Sensitive data is removed, and structured findings are extracted.

3. **AI-Powered Report Generation**  
   A prompt-based system sends the structured data to the OpenAI GPT API, which returns a text section for the radiology report, following RSNA guidelines.

4. **Database Storage**  
   The data is stored in a PostgreSQL database via SQLAlchemy.

5. **Web Interface (coming soon)**  
   Users can log in, upload files, and access report results through a secure interface.

---

## 🗃️ Database Schema Overview

Your SQLAlchemy models reflect a modular, normalized schema:

- `Users`: User account management  
- `PDF_IMAGE_ANALYSIS_DATA`: Raw PDF upload data and metadata  
- `PROCESSED_IMAGE_ANALYSIS_DATA`: AI-generated report text and metadata  
- `FINDINGS`: Extracted values from the image analysis (e.g., SUVmax, volume)  
- `ERROR_LOGS`: Captures pipeline or API errors  

---

## 🔐 Intended Use

This project is built to integrate into **radiological diagnostic workflows** where structured outputs (e.g., from volumetric brain tools or PET/CT pipelines) are increasingly used. It provides:
- A fast way to convert AI output into **RSNA-style free text**
- Structured **short and long reports** for radiologist review
- A future-proof structure for adding other modalities and body regions

---

## 🧪 Status & Roadmap

- Flask backend and SQLAlchemy models  
- Secure user system
- Database logging of findings and errors
- GUI for web upload and preview  
- PACS and RIS integration features  
- Export to HL7 / DICOM-SR / PDF  
- Deployment via Docker  

---

## 📄 License

This project is intended for research and clinical prototyping. Licensing details to be defined.

## 🤝 Contributions

Contributions, feedback, and collaboration are welcome. Let’s build tools that support radiologists and improve patient care.

---

## 👤 Author

**Richard Nürnberger**  
AI Engineering | Medical Imaging | Radiological Technologies
