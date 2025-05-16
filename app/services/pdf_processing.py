from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import fitz
from io import BytesIO
import pytesseract
from PIL import Image
import io

# Load the environment variable from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Explicit Path to tesseract (homebrew)
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"


def extract_pdf_content(pdf_blob, lang="deu"): # 'deu', 'eng', 'fra', ...
    """
    Perform OCR on all pages of a PDF to extract textual content.

    Args:
        pdf_blob (bytes): The binary content of the PDF file.
        lang (str): Language(s) for Tesseract OCR. Default is 'eng'.

    Returns:
        str: Extracted text from all pages, cleaned and concatenated.
    """
    text_output = []
    pdf_document = fitz.open(stream=pdf_blob, filetype="pdf")

    for page_index in range(len(pdf_document)):
        page = pdf_document.load_page(page_index)

        # Render page as image (high resolution for OCR)
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        # Run OCR
        ocr_text = pytesseract.image_to_string(img, lang=lang)

        if ocr_text.strip():  # Only add non-empty OCR results
            text_output.append(f"--- Page {page_index + 1} ---\n{ocr_text.strip()}")

    # Combine and clean text
    full_text = "\n\n".join(text_output).strip()
    return full_text


def build_prompt(text_data):


    print("/n/n/nExtracted PDF-Text:/n(build_prompt)", text_data)

    return (
        "You are a radiology expert. The following is an extracted output from an AI-assisted medical image analysis report:"
        "Analyze the following radiological findings and return a JSON object with the keys: "
        "`company`, `sequences`, `method`, `region`, `modality`, `short_text`, `long_text`, `quality`.\n\n"
        f"{text_data}"
    )


def call_openai(prompt):
    response = client.chat.completions.create(model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.2)
    content = response.choices[0].message.content


    print("(call_openai) - Prompt:", content)

    try:
        # Try to parse the output into a dictionary
        data = json.loads(content)
        return data
    except json.JSONDecodeError:
        raise ValueError("OpenAI did not return valid JSON. Please ensure your prompt asks for JSON output.")
    # return {
    #     'company': 'Generic AI Co.',
    #     'sequences': 'T1, T2, FLAIR',
    #     'method': 'AI-supported image summarization',
    #     'region': 'Thorax',
    #     'modality': 'X-Ray',
    #     'short_text': content[:160],
    #     'long_text': content,
    #     'quality': "0.95"
    # }