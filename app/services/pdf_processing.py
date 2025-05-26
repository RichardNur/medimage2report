from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import fitz
import pytesseract
from PIL import Image, ImageOps
import io
import re
import logging



# Load the environment variable from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Explicit Path to tesseract (homebrew)
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"



def extract_pdf_content(pdf_blob: bytes, lang: str = "deu") -> dict:
    """
    Perform OCR on all pages of a PDF to extract textual content.

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
    pdf_document = fitz.open(stream=pdf_blob, filetype="pdf")

    for page_index in range(len(pdf_document)):
        page = pdf_document.load_page(page_index)
        pix = page.get_pixmap(dpi=400)

        img = Image.open(io.BytesIO(pix.tobytes("png")))

        # Convert to grayscale and enhance contrast
        img = ImageOps.grayscale(img)
        # img = ImageOps.autocontrast(img)  # Optional tweak

        # Run OCR
        try:
            ocr_text = pytesseract.image_to_string(img, lang=lang).strip()
        except pytesseract.TesseractError as e:
            logging.error(f"Tesseract OCR failed on page {page_index + 1}: {e}")
            ocr_text = ""

        if not ocr_text:
            logging.warning(f"OCR returned empty text on page {page_index + 1}")

        text_pages.append({
            "page": page_index + 1,
            "text": ocr_text
        })

    # Combine full cleaned text
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
        "You are a radiologist assisting in generating a structured report. "
        "The content below was extracted from a PDF file, which summarizes results from an AI-assisted image analysis tool. "
        "This tool reviewed DICOM images and automatically identified potential abnormalities or findings. "
        "You do NOT have access to the actual imaging, so only include information clearly present in the extracted text.\n\n"

        "Use RSNA structured reporting style and terminology when possible.\n\n"

        "**Instructions:**\n"
        "- Provide two descriptions: a short version (for the physician’s report) and a long version (simplified for the patient)."
        "- The short text is for implementing into the radiological report, within the description section. Make sure"
        "to mention the company, method, sequence and especially findings for comprehensiveness. If there are references like image number, also mention these.\n"
        "- Only fill fields if you are confident. If unsure, leave the field out.\n"
        "- Return ONLY valid JSON in the following structure:\n\n"
        "```json\n"
        "{\n"
        "  \"company\": string,\n"
        "  \"sequences\": [string, ...],\n"
        "  \"method\": string,\n"
        "  \"region\": string,\n"
        "  \"modality\": string,\n"
        "  \"short_text\": string,\n"
        "  \"long_text\": string,\n"
        "  \"quality\": string\n"
        "}\n"
        "```\n\n"

        "Here is the extracted text from the PDF:\n\n"
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