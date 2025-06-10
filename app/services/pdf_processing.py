from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import logging
import fitz
import pytesseract
import io
import re
from PIL import Image, ImageOps, ImageFilter, ImageEnhance


# Load the environment variable from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Explicit Path to tesseract (homebrew)
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"


def extract_pdf_content(pdf_blob: bytes, lang: str = "deu") -> dict:
    """
    Perform enhanced OCR on all pages of a PDF to extract textual content.
    Applies grayscale, sharpening, contrast enhancement, and deduplication.

    Args:
        pdf_blob (bytes): The binary content of the PDF file.
        lang (str): Language(s) for Tesseract OCR, e.g. 'deu', 'eng'.

    Returns:
        dict: {
            'raw_text': str (all pages concatenated),
            'pages': list of dicts [{page: int, text: str}],
            'language': str (lang used),
        }
    """
    text_pages = []
    seen_lines_global = set()

    pdf_document = fitz.open(stream=pdf_blob, filetype="pdf")

    for page_index in range(len(pdf_document)):
        page = pdf_document.load_page(page_index)
        pix = page.get_pixmap(dpi=400)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        # Preprocessing
        img = ImageOps.grayscale(img)
        img = img.filter(ImageFilter.SHARPEN)
        img = ImageEnhance.Contrast(img).enhance(2.0)

        try:
            ocr_text = pytesseract.image_to_string(img, lang=lang)
        except pytesseract.TesseractError as e:
            logging.error(f"Tesseract OCR failed on page {page_index + 1}: {e}")
            ocr_text = ""

        # Clean and deduplicate lines
        lines = []
        for line in ocr_text.splitlines():
            line = line.strip()
            if not line or re.fullmatch(r"[_\-\s]+", line):
                continue
            normalized = re.sub(r"\s+", " ", line)
            if normalized not in seen_lines_global:
                seen_lines_global.add(normalized)
                lines.append(normalized)

        page_text = "\n".join(lines)
        text_pages.append({
            "page": page_index + 1,
            "text": page_text
        })

    full_text = "\n\n".join([f"--- Page {p['page']} ---\n{p['text']}" for p in text_pages if p['text']]).strip()

    return {
        "raw_text": full_text,
        "pages": text_pages,
        "language": lang
    }


def build_prompt(structured_data: dict) -> str:
    """
    Build a structured OpenAI prompt from extracted OCR text,
    requesting a strictly formatted JSON response with content in both English and German.
    """
    # Ensure we safely extract the raw text string
    extracted_text = structured_data.get("raw_text", "")
    if not isinstance(extracted_text, str):
        extracted_text = str(extracted_text)

    # Normalize whitespace
    extracted_text = extracted_text.strip()

    return (
    "You are a radiologist and language model assistant. Your task is to generate structured report content "
    "based solely on the extracted text from a PDF file. This PDF contains output from an AI-based medical image analysis system, "
    "which has processed DICOM data and presented findings in both text and tables. The source text may be in English or German.\n\n"

    "**Context and Constraints:**\n"
    "- You do NOT have access to the original images—only to the extracted PDF text.\n"
    "- The data may include measurement tables, classifications (e.g., BI-RADS, Bone-RADS), percentile values, confidence intervals, and anatomical terms.\n"
    "- Handle medical terminology with precision and prioritize factual correctness.\n"
    "- If information is ambiguous or missing, omit that field instead of guessing.\n"
    "- Special care must be taken to interpret tables and associated units correctly to avoid clinical misinterpretation.\n\n"

    "**Output Requirements:**\n"
    "You must return a SINGLE JSON object that strictly follows this structure. The textual report content MUST be provided in both English and German.\n"
    "```json\n"
    "{\n"
    "  \"company\": \"string\",                 // e.g. 'mediaire'\n"
    "  \"sequences\": [\"string\", ...],        // e.g. [\"Accelerated Sag IR-FSPGR (T1)\", \"tse2d1_3\"]\n"
    "  \"method\": \"string\",                  // e.g. 'AI-assisted volumetry using mdbrain v4.7.0'\n"
    "  \"region\": \"string\",                  // e.g. 'Brain', 'Spine lumbar'\n"
    "  \"modality\": \"string\",                // e.g. 'MR', 'CT'\n"
    "  \"short_text_en\": \"string\",           // RSNA-style summary for radiology report integration, in ENGLISH.\n"
    "  \"long_text_en\": \"string\",            // Layperson-friendly version of the above, in ENGLISH.\n"
    "  \"short_text_de\": \"string\",           // RSNA-style summary for radiology report integration, in GERMAN (Befund-Stil).\n"
    "  \"long_text_de\": \"string\",            // Layperson-friendly version of the above, in GERMAN (laienfreundliche Sprache).\n"
    "  \"quality\": \"string\"                  // e.g. 'Good', 'Insufficient resolution', or comments from quality control\n"
    "}\n"
    "```\n\n"

    "**Generation Instructions:**\n"
    "- First, Carefully read and internally structure the extracted PDF text.\n"
    "- Then, Identify findings (e.g. lesions found), quantitative values (e.g. volumes, percentiles), methods used, and any classifications.\n"
    "- In the `short_text_en`, write a concise, professional summary in English suitable for a radiology report. Include company, method, and key findings.\n"
    "- In the `long_text_en`, explain the same findings in accessible English terms for patients.\n"
    "- In the `short_text_de`, write a concise, professional summary in German suitable for a radiology report (im Stil eines ärztlichen Befundes).\n"
    "- In the `long_text_de`, explain the same findings in accessible German terms for patients (in einer für Laien verständlichen Sprache).\n\n"

    "Begin your analysis using the following extracted text:\n\n"
    f"\"{extracted_text}\""
)


def call_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    content = response.choices[0].message.content

    try:
        # Remove ```json and ``` if present
        cleaned = re.sub(r"```json|```", "", content).strip()
        data = json.loads(cleaned)
        return data
    except json.JSONDecodeError as e:
        print("JSONDecodeError:", str(e))
        raise ValueError("OpenAI did not return valid JSON. Prompt might need refinement.")


def call_gemini(prompt):
    import google.generativeai as genai

    # Configure the client with your API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")

    # Generate a response using the Gemini API
    response = model.generate_content(prompt)
    text = response.text

    # 2) Strip ```json and ``` if present
    cleaned = re.sub(r"```json|```", "", text).strip()

    # 3) Parse to dict
    try:
        data = json.loads(cleaned)
        return data
    except json.JSONDecodeError as e:
        # Optionally log raw text and the exception
        print("Gemini raw response:", repr(text))
        print("Cleaned for JSON:", repr(cleaned))
        raise ValueError("Gemini did not return valid JSON.") from e




