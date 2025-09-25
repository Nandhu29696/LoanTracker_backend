import fitz
import re
import pytesseract
from PIL import Image
import io
from .models import ExtractedField

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text(page):
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img)


def detect_document_type(doc):
    footer_text = ""
    for page in doc:
        blocks = page.get_text("blocks")
        page_height = page.rect.height
        for block in blocks:
            x0, y0, x1, y1, text, *_ = block
            if y0 > page_height * 0.85:
                footer_text += " " + text
    ft = footer_text.lower()
    if "loan estimate" in ft:
        return "Loan Estimate"
    if "closing disclosure" in ft:
        return "Closing Disclosure"
    return "Miscellaneous"


def process_document(document):
    doc = fitz.open(document.file.path)
    doc_type = detect_document_type(doc)

    extracted, _ = ExtractedField.objects.get_or_create(document=document)
    extracted.document_type = doc_type

    for page_index in range(len(doc)):
        text = extract_text(doc[page_index])

        # ---------- Loan Estimate ----------
        if doc_type == "Loan Estimate" and page_index == 1:
            match = re.search(r"Loan Amount\s+\$?([\d,]+)", text)
            if match:
                extracted.loan_amount = match.group(1)

            match = re.search(r"DATE ISSUED\s+([\d/]+)", text, re.IGNORECASE)
            if match:
                extracted.date_issued = match.group(1)

            match = re.search(r"Loan Term\s+(\d+ years?)", text, re.IGNORECASE)
            if match:
                extracted.loan_term = match.group(1)

            match = re.search(r"Interest Rate\s+([\d.]+%)", text, re.IGNORECASE)
            if match:
                extracted.interest_rate = match.group(1)

            match = re.search(r"APR\s+([\d.]+%)", text, re.IGNORECASE)
            if match:
                extracted.apr = match.group(1)

        # ---------- Closing Disclosure ----------
        if doc_type == "Closing Disclosure":
            match = re.search(r"Closing Date\s+([\d/]+)", text, re.IGNORECASE)
            if match:
                extracted.closing_date = match.group(1)

            match = re.search(r"Disbursement Date\s+([\d/]+)", text, re.IGNORECASE)
            if match:
                extracted.disbursement_date = match.group(1)

            match = re.search(r"Sale Price\s+\$?([\d,]+)", text, re.IGNORECASE)
            if match:
                extracted.sales_price = match.group(1)

        # ---------- Form 1009: Reverse Mortgage Application ----------
        if "Residential Loan Application for Reverse Mortgages" in text:
            extracted.document_type = "Form 1009"

            borrower_match = re.search(r"Borrower\s+([A-Za-z\s\.\-]+)\s+\d{1,2}/\d{1,2}/\d{2,4}", text)
            if borrower_match:
                extracted.borrower_name = borrower_match.group(1).strip()

            coborrower_match = re.search(r"Co-Borrower\s+([A-Za-z\s\.\-]+)", text)
            if coborrower_match:
                extracted.coborrower_name = coborrower_match.group(1).strip()

            date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", text)
            if date_match:
                extracted.application_date = date_match.group(1)

            address_match = re.search(r"(\d+\s+THE VILLAGE[^\n]+)", text, re.IGNORECASE)
            if address_match:
                extracted.property_address = address_match.group(1).strip()

            value_match = re.search(r"Estimate of Appraised Value:\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
            if value_match:
                extracted.appraised_value = value_match.group(1)

            fee_match = re.search(r"Loan Origination Fee\s*\$?([\d,]+\.\d{2})", text, re.IGNORECASE)
            if fee_match:
                extracted.origination_fee = fee_match.group(1)

    extracted.save()
    return extracted
