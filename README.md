# 🧠 Medical Report Generation from Image Analysis Outputs  
### Convert PDF with Medical Image Evaluation to Structured Medical Report Text  

## 📌 Problem

Modern radiology workflows increasingly incorporate various image analysis tools and AI applications. These systems commonly perform classification and segmentation tasks, producing outputs in formats such as **PDF** and **DICOM**.

While these outputs enhance diagnostic precision, they are typically stored in the **PACS** and must be manually reviewed by radiologists. This adds to their workload when generating comprehensive reports for referring physicians.

## 💡 Solution

This project aims to **support radiologists** by integrating and organizing outputs from multiple image analysis applications. The core idea is to transform image analysis outputs—such as brain lesion detection—into **professional, structured text** suitable for inclusion in medical reports, following **RSNA reporting guidelines**.

### 🔄 Workflow Overview

1. **Anonymization**  
   Patient data is anonymized to comply with privacy standards.

2. **Preprocessing**  
   Image analysis results are extracted and prepared for language model interpretation.

3. **Report Generation via OpenAI API**  
   A prompt-based system interacts with the OpenAI API to generate clear, clinically structured text summarizing the findings.

## 🎯 Intended Use

This tool is designed for integration into the **medical reporting workflow**. It aims to streamline the process of incorporating AI-generated analysis into radiologist reports, reducing workload and enhancing reporting consistency.

---

## 🛠️ Coming Soon

- Installation Instructions  
- Example Outputs  
- Configuration & API Integration Guide  
- GUI and PACS Workflow Integration (planned)

---

## 📄 License

This project is intended for research and clinical prototyping. Licensing details to be defined.

## 🤝 Contributions

Contributions, feedback, and collaboration are welcome. Let’s build tools that support radiologists and improve patient care.

---

## 👤 Author

**Richard Nürnberger**  
AI Engineering | Medical Imaging | Radiological Technologies
