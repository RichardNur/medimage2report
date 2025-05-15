from PyPDF2 import PdfReader
from io import BytesIO
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# Load the environment variable from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_pdf_text(pdf_blob):
    reader = PdfReader(BytesIO(pdf_blob))

    print(list(reader.pages))

    text = ''
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + '\n'
    return text.strip()


def build_prompt(text_data):

    print("(build_prompt) - Extracted PDF-Text:", text_data)

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