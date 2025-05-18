# 🧠 medimage2report: AI-Powered Radiology Report Generation  
### Transform AI-Analyzed Medical Images into Structured RSNA-Compliant Reports

---

## 📌 Overview

As artificial intelligence (AI) becomes increasingly integral to medical imaging, radiologists are often tasked with integrating AI-generated findings into structured diagnostic reports.  
**medimage2report** is designed to streamline this process by converting AI analysis outputs—typically delivered in PDF format by tools such as *mediaire*, *deepc*, or *quibim*—into clear, RSNA-compliant report sections.

By integrating medimage2report into your workflow, you can:
- Reduce manual documentation workload,
- Improve consistency across reports,
- Save time—especially when managing high volumes of AI outputs.

---

## 🔄 Workflow Overview

1. **PDF Upload**  
   Upload AI-generated analysis reports (e.g., brain volumetry, PET/CT, etc.).

2. **Anonymization & Extraction**
   (Note: anonymization module is currently under development)
   Sensitive data is removed. Relevant findings are extracted from the file.

4. **AI-Powered Report Generation**  
   The structured input is sent to the GPT engine, which generates RSNA-style radiology report text (short + long version).

5. **Database Storage**  
   All data—PDFs, metadata, and report outputs—are stored securely via SQLAlchemy in a PostgreSQL database.

6. **Web Interface**  
   Users log in to view, manage, and download their reports via a clean and secure interface.

---

## 🔐 Intended Use

This project integrates into **radiological reporting workflows** where AI tools are used for pre-analysis, but their results are delivered as static files.  
**medimage2report** offers:

- 📄 RSNA-compliant report sections auto-generated from AI tool output  
- 🧠 Structured summary + full-length report text for radiologists to review  
- 📂 Fast integration for neuroradiology, oncology, MSK, and thoracic imaging  
- 🧰 Expandable support for DICOM, HL7, and future AI tools

---

## 🧪 Status & Roadmap

| Feature                          | Status       |
|----------------------------------|--------------|
| Flask backend (modular routes)   | ✅ Implemented |
| User authentication (Flask-Login)| ✅ Implemented |
| PDF upload & AI extraction       | ✅ Implemented |
| GPT-based RSNA text generation   | ✅ Implemented |
| Web interface for uploads        | ✅ Live        |
| Error logging                    | ✅ Live        |
| TBC Recognizer (DICOM Upload)    | 🔄 Planned     |
| PACS/RIS integration             | 🔄 Planned     |
| Export: DICOM-SR / HL7 / PDF     | 🔄 Planned     |
| Docker deployment                | 🔄 Planned     |

---

## 💻 Live Demo

Visit the hosted demo:  
🔗 **[shaire.pythonanywhere.com](https://shaire.pythonanywhere.com/)**  
*(Note: hosted version may have limited compute resources for OCR and GPT calls)*

---

## 📄 License

This project is intended for **research and clinical prototyping**. Licensing terms are under review and will be provided in a future update.

---

## 🤝 Contributions

We welcome contributions from radiologists, AI developers, and healthcare engineers.  
Whether through feedback, clinical use cases, or code—your support improves this tool.

---

## 👤 Author

**Richard Nürnberger**  
AI Engineering | Medical Imaging | Radiological Technologies  
📧 [Richard_Nuernberger@outlook.com](mailto:Richard_Nuernberger@outlook.com)
