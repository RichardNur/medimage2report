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
from pytesseract import TesseractError

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
    requesting a strictly formatted JSON response.
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
    "which has processed DICOM data and presented findings in both text and tables, it might be in German Language, too.\n\n"

    "**Context and Constraints:**\n"
    "- You do NOT have access to the original images—only to the extracted PDF text.\n"
    "- The data may include measurement tables, classifications (e.g., BI-RADS, Bone-RADS), percentile values, confidence intervals, and anatomical terms.\n"
    "- Handle medical terminology with precision and prioritize factual correctness.\n"
    "- If information is ambiguous or missing, omit that field instead of guessing.\n"
    "- Special care must be taken to interpret tables and associated units correctly to avoid clinical misinterpretation.\n\n"

    "**Output Requirements:**\n"
    "You must return a JSON object that strictly follows this structure:\n"
    "```json\n"
    "{\n"
    "  \"company\": string,                 // e.g. 'mediaire', 'Aidoc', 'Floy', 'Incepto'\n"
    "  \"sequences\": [string, ...],        // e.g. ['Accelerated Sag IR-FSPGR (T1)', 'tse2d1_3']\n"
    "  \"method\": string,                  // e.g. 'AI-assisted volumetry using mdbrain v4.7.0'\n"
    "  \"region\": string,                  // e.g. 'Brain', 'Spine lumbar', 'Supratentorial'\n"
    "  \"modality\": string,                // e.g. 'MR', 'CT'\n"
    "  \"short_text\": string,              // RSNA-style summary for radiology report integration\n"
    "  \"long_text\": string,               // Layperson-friendly version of the above\n"
    "  \"quality\": string                  // e.g. 'Good', 'Insufficient resolution', or comments from quality control\n"
    "}\n"
    "```\n\n"

    "**Generation Instructions:**\n"
    "- First, Carefully read and internally structure the extracted PDF text.\n"
    "- Then, Identify findings (e.g. lesions found), quantitative values (e.g. volumes, percentiles), methods used, and any classifications."
    "- If tables are included, extract values with correct units and associate them with the proper anatomical regions.\n"
    "- Cross-reference repeated or redundant values. Only include the most complete and correct version.\n"
    "- In the *short_text*, include company, method, modality, sequence/series, region, and key findings. Mention image numbers if available.\n"
    "- In the *long_text*, explain the same findings in accessible terms for patients, including comparisons if available (e.g. “reduced hippocampus volume compared to previous study”).\n\n"

    "Begin your analysis using the following extracted text:\n\n"
    f"{extracted_text}"
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