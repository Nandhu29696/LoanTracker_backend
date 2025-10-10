import os
import fitz 
import re
import pytesseract
from PIL import Image
import io
import pandas as pd
import json
from collections import defaultdict

# === Folder containing all PDFs ===
folder_path = r"D:\project\Python\Data Encrtption\dataextraction\pdf"

# === Text extraction  ===
def extract_text(page):
    pix = page.get_pixmap(dpi=300)  # render page at 300 DPI
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    text = pytesseract.image_to_string(img)  # OCR extraction
    return text

#====Text extraction====
def extract_text_layer(page):
    """Use text layer only (cleaned up for regex use)."""
    text = page.get_text("text")
    return text

# === Helper: print field and value (used during extraction) ===
def print_field(field, value):
    print(f"{field}: {value}")

# === Extract footer text (for document type detection) ===
def get_footer_text(doc):
    footer_text = ""
    for page in doc:
        blocks = page.get_text("blocks")
        page_height = page.rect.height
        for block in blocks:
            x0, y0, x1, y1, text, *_ = block
            if y0 > page_height * 0.85:  # bottom 15% of page
                footer_text += " " + text
    return footer_text.strip()

# === Detect document type from footer ===
def detect_document_type(doc):
    footer_text = get_footer_text(doc).lower()
    conditions = [
        ("Loan Estimate", "loan estimate" in footer_text),
        ("Closing Disclosure", "closing disclosure" in footer_text),
        ("1003 Application", "uniform residential loan application" in footer_text or "fannie mae form 1003" in footer_text),
        ("Final 1009", "fannie mae form 1009" in footer_text or "form 1009" in footer_text),
        ("Appraisal Report", "clickforms appraisal software" in footer_text),
        ("Fee Worksheet", "calyx form" in footer_text),
        ("Ticor Title", "ticor title company of california" in footer_text or "clta preliminary report form" in footer_text),
    ]
    for doc_type, condition in conditions:
        if condition:
            return doc_type
    return "Miscellaneous"

# === Example extraction for Loan Estimate (Page 1 only) ===
def extract_loan_estimate_data(doc, filename, all_data):
    for page_index in range(len(doc)):
        text = extract_text(doc[page_index])

        if  page_index == 1:  # Process  Page 1 
            
            # ---extract Loan Amount---
            match = re.search(r"Loan Amount\s+\$?([\d,]+)", text)
            if match:
                value = "$" + match.group(1).replace(" ", "").strip()
                all_data.append(["Loan Amount", value, filename, page_index + 1])
            
            # --- DATE ISSUED ---
            match = re.search(r"DATE ISSUED\s+([\d/]+)", text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                all_data.append(["Date Issued", value, filename, page_index + 1])
                

            # --- PROPERTY ---
            match = re.search(r"PROPERTY\s+([\s\S]*?)SALE PRICE", text, re.IGNORECASE) 
            if match: 
                value = match.group(1).strip().replace("\n", " ") 
                all_data.append(["Property", value, filename, page_index + 1])

            # --- SALE PRICE ---
            match = re.search(r"SALE PRICE\s+\$?([\d,]+)", text, re.IGNORECASE)
            if match:
                value = "$" + match.group(1).strip()
                all_data.append(["Sale Price", value, filename, page_index + 1])
                

            # --- LOAN TERM ---
            match = re.search(r"LOAN TERM\s+([^\n]+)", text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                all_data.append(["Loan Term", value, filename, page_index + 1])
                

            # --- PURPOSE ---
            match = re.search(r"PURPOSE\s+(\S+)", text, re.IGNORECASE)
            if match:
                purpose_value = match.group(1).strip()
                all_data.append(["Purpose", purpose_value, filename, page_index + 1])

            # --- PRODUCT ---
            match = re.search(r"PRODUCT\s+([^\n]+)", text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                all_data.append(["Product", value, filename, page_index + 1])
            

            # --- LOAN TYPE ---
            text_layer = extract_text_layer(doc[page_index])  # use only text layer
            match = re.search(r"LOAN TYPE\s+([^\n]+)", text_layer, re.IGNORECASE)
            if match:
                line = match.group(1).strip()
    
                # Find the option that has an 'x' in front of it
                loan_type_match = re.search(r"x\s*([A-Za-z]+)", line)
                if loan_type_match:
                    value = loan_type_match.group(1).strip()
                else:
                    value = line  # fallback: store the full line if no 'x' found
                all_data.append(["Loan Type", value, filename, page_index + 1])
            
            # --- RATE LOCK  ---

            match = re.search(r"RATE LOCK\s+([^\n]+(?:\n[^\n]+)?)", text_layer, re.IGNORECASE)#use only text layer
            if match:
                line = match.group(1).replace("\n", " ").strip()  # merge multiple lines

                # Detect the word immediately after 'x'
                rate_lock_match = re.search(r"x\s+([^\s,]+)", line)  # take first word after x
                if rate_lock_match:
                    value = rate_lock_match.group(1).strip()
                else:
                    value = line  # fallback if no x found
                all_data.append(["Rate Lock", value, filename, page_index + 1])
            
            # --- ESTIMATED CLOSING COSTS ---
            match = re.search(r"Estimated Closing Costs\s+\$?([\d,]+)", text, re.IGNORECASE)
            if match:
                value = "$" + match.group(1).replace(" ", "").strip()
                all_data.append(["Estimated Closing Costs", value, filename, page_index + 1])


            # --- ESTIMATED CASH TO CLOSE ---
            match = re.search(r"Estimated Cash to Close\s+\$?([\d,]+)", text, re.IGNORECASE)
            if match:
                value = "$" + match.group(1).replace(" ", "").strip()
                all_data.append(["Estimated Cash to Close", value, filename, page_index + 1])

        elif    page_index==2:
                
                # --- A. Origination Charges ---
                match = re.search(r"A\.\s+Origination Charges\s+\$?([\d,]+)", text, re.IGNORECASE)
                if match:
                    value = "$" + match.group(1).replace(" ", "").strip()
                    all_data.append(["Origination Charges", value, filename, page_index + 1])

                # --- B. Services You Cannot Shop For ---
                match = re.search(r"B\.\s+Services You Cannot Shop For\s+\$?([\d,]+)", text, re.IGNORECASE)
                if match:
                    value = "$" + match.group(1).replace(" ", "").strip()
                    all_data.append(["Services You Cannot Shop For", value, filename, page_index + 1])

                # --- C. Services You Can Shop For ---
                match = re.search(r"C\.\s+Services You Can Shop For\s+\$?([\d,]+)", text, re.IGNORECASE)
                if match:
                    value = "$" + match.group(1).replace(" ", "").strip()
                    all_data.append(["Services You Can Shop For", value, filename, page_index + 1])

                # --- D. TOTAL LOAN COSTS (A + B + C) ---
                match = re.search(r"D\.\s+TOTAL LOAN COSTS\s*\(A \+ B \+ C\)\s+\$?([\d,]+)", text, re.IGNORECASE)
                if match:
                    value = "$" + match.group(1).replace(" ", "").strip()
                    all_data.append(["Total Loan Costs", value, filename, page_index + 1])

                # --- I. TOTAL OTHER COSTS (E + F + G + H) ---
                match = re.search(r"I\.\s+TOTAL OTHER COSTS\s*\(E \+ F \+ G \+ H\)\s+\$?([\d,]+)", text, re.IGNORECASE)
                if match:
                    value = "$" + match.group(1).replace(" ", "").strip()
                    all_data.append(["Total Other Costs", value, filename, page_index + 1])

                # --- J. TOTAL CLOSING COSTS ---
                match = re.search(r"J\.\s+TOTAL CLOSING COSTS\s+\$?([\d,]+)", text, re.IGNORECASE)
                if match:
                    value = "$" + match.group(1).replace(" ", "").strip()
                    all_data.append(["Total Closing Costs", value, filename, page_index + 1])

                # --- Estimated Cash to Close ---
                match = re.search(r"Estimated Cash to Close\s+\$?([\d,]+)", text, re.IGNORECASE)
                if match:
                    value = "$" + match.group(1).replace(" ", "").strip()
                    all_data.append(["Estimated Cash to Close", value, filename, page_index + 1])
        elif    page_index==3:
                
                # --- LENDER NAME ---
                match = re.search(r"LENDER\s+([^\n]+)", text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip().replace("\n", " ")
                    all_data.append(["Lender Name", value, filename, page_index + 1])

                # --- LOAN OFFICER NAME ---
                match = re.search(r"LOAN OFFICER\s+([^\n]+)", text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip().replace("\n", " ")
                    all_data.append(["Loan Officer Name", value, filename, page_index + 1])

                # --- LOAN OFFICER EMAIL ---
                match = re.search(r"EMAIL\s+([\S]+)", text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    all_data.append(["Loan Officer Email", value, filename, page_index + 1])

                # --- LOAN OFFICER PHONE ---
                match = re.search(r"PHONE\s+([\d-]+)", text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    all_data.append(["Loan Officer Phone", value, filename, page_index + 1])

def extract_closing_disclosure_data(doc, filename, all_data):
    for page_index in range(len(doc)):
        text = extract_text(doc[page_index])

        if page_index == 1:

            # Loan Amount
            match = re.search(r"Loan Amount\s*\$?([\d,\.]+)", text, re.IGNORECASE | re.DOTALL)
            value = "$" + match.group(1) if match else "Loan Amount not found"
            all_data.append(["Loan Amount", value, filename, page_index + 1])
            
            # Interest Rate
            match = re.search(r"Interest Rate\s*([\d\.%]+)", text, re.IGNORECASE | re.DOTALL)
            value = match.group(1) if match else "Interest Rate not found"
            all_data.append(["Interest Rate", value, filename, page_index + 1])

            # Product
            match = re.search(r"Product\s*([\s\S]*?)\n", text, re.IGNORECASE)
            value = match.group(1).strip() if match else "Product not found"
            all_data.append(["Product", value, filename, page_index + 1])

            # Purpose
            match = re.search(r"Purpose\s*([\s\S]*?)\n", text, re.IGNORECASE)
            value = match.group(1).strip() if match else "Purpose not found"
            all_data.append(["Purpose", value, filename, page_index + 1])
        
        elif    page_index==2:
                
                # === A. Origination Charges ===
                match = re.search(r"A\.\s+Origination Charges\s*([\s\S]*?)\n", text, re.IGNORECASE)
                value = match.group(1).strip() if match else "Origination Charges not found"
                all_data.append(["Origination Charges", value, filename, page_index + 1])

                # === C. Services Borrower Did Shop For ===
                match = re.search(r"C\.\s+Services Borrower Did Shop For\s*([\s\S]*?)\n", text, re.IGNORECASE)
                value = match.group(1).strip() if match else "Services Borrower Did Shop For not found"
                all_data.append(["Services Borrower Did Shop For", value, filename, page_index + 1])

                # === G. Initial Escrow Payment at Closing ===
                match = re.search(r"G\.\s+Initial Escrow Payment at Closing\s*([\s\S]*?)\n", text, re.IGNORECASE)
                value = match.group(1).strip() if match else "Initial Escrow Payment not found"
                all_data.append(["Initial Escrow Payment at Closing", value, filename, page_index + 1])

                # === I. TOTAL OTHER COSTS (Borrower-Paid) ===
                match = re.search(r"I\.\s+TOTAL OTHER COSTS.*?\n\s*\$?([\d,\.]+)", text, re.IGNORECASE)
                value = "$" + match.group(1).strip() if match else "Total Other Costs not found"
                all_data.append(["Total Other Costs", value, filename, page_index + 1])
        
        elif    page_index==3:
                
                # --- K. TOTAL PAYOFFS AND PAYMENTS ---
                match = re.search(r"K\.\s+TOTAL PAYOFFS AND PAYMENTS\s*[\n$-]*\$?([\d,\.]+)", text, re.IGNORECASE)
                value = "$" + match.group(1).strip() if match else "Total Payoffs and Payments not found"
                all_data.append(["Total Payoffs and Payments", value, filename, page_index + 1])

        elif    page_index==4:
               
                # --- Initial Escrow Payment ---
                match = re.search(r"Initial Escrow\s*Payment\s*\$?([\d,\.]+)", text, re.IGNORECASE)
                value = "$" + match.group(1).strip() if match else "Initial Escrow Payment not found"
                all_data.append(["Initial Escrow Payment", value, filename, page_index + 1])

        
def extract_appraisal_data(doc, filename, all_data):
    for page_index in range(len(doc)):
        text = extract_text(doc[page_index])

        if page_index == 0:  # extract only from first page

            # === Property Address Extraction ===
            match = re.search(
                r"Property\s*Address\s*City\s+([A-Za-z\s]+?)\s+State\s+([A-Z]{2})",
                text, re.IGNORECASE
            )
            value = f"City: {match.group(1).strip()}, State: {match.group(2).strip()}" if match else "Property Address not found"
            all_data.append(["Property Address", value, filename, page_index])

            # === Tax Year ===
            match = re.search(r"Tax Year\s*:?(\d{4})", text, re.IGNORECASE)
            value = match.group(1) if match else "Tax Year not found"
            all_data.append(["Tax Year", value, filename, page_index])

            # === Census Tract ===
            match = re.search(r"Census Tract\s*:?([\d./ ]+)", text, re.IGNORECASE)
            value = match.group(1).strip() if match else "Census Tract not found"
            all_data.append(["Census Tract", value, filename, page_index])

            # === Property Rights Appraised ===
            match = re.search(r"Property Rights Appraised.*?\[x\]\s*([A-Za-z ]+)", text, re.IGNORECASE | re.DOTALL)
            value = match.group(1).strip() if match else "Property Rights Appraised not found"
            all_data.append(["Property Rights Appraised", value, filename, page_index])

            # === Neighborhood Name ===
            match = re.search(r"Neighborhood Name\s*([A-Za-z/\- ]+)", text, re.IGNORECASE)
            value = match.group(1).strip() if match else "Neighborhood Name not found"
            all_data.append(["Neighborhood Name", value, filename, page_index])

            # === Assignment Type ===
            match = re.search(r"Assignment Type\s*(?:\[[xX]\|\s*)?([A-Za-z ]+?)(?=\s*\[|$)", text, re.IGNORECASE)
            value = match.group(1).strip() if match else "Assignment Type not found"
            all_data.append(["Assignment Type", value, filename, page_index])

            # === Currently Offered for Sale ===
            match = re.search(r"offered for sale.*?\[\s*X\s*\]\s*Yes", text, re.IGNORECASE | re.DOTALL)
            value = "Yes" if match else "No"
            all_data.append(["Currently Offered for Sale", value, filename, page_index])

            # === Data Source (MLS) ===
            match = re.search(r"MLS[#\s]*([\d]+)", text, re.IGNORECASE)
            value = "MLS #" + match.group(1) if match else "Data Source not found"
            all_data.append(["Data Source", value, filename, page_index])

            # === List Date ===
            match = re.search(r"List date\s*([0-9/]+)", text, re.IGNORECASE)
            value = match.group(1) if match else "List Date not found"
            all_data.append(["List Date", value, filename, page_index])

            # === Seller is Owner of Record ===
            match = re.search(r"property seller.*owner of public record.*?\[\s*X\s*\]\s*Yes", text, re.IGNORECASE | re.DOTALL)
            value = "Yes" if match else "No"
            all_data.append(["Seller is Owner of Record", value, filename, page_index])

            # === Financial Assistance ===
            match = re.search(r"financial assistance.*?\[\s*X\s*\]\s*No", text, re.IGNORECASE | re.DOTALL)
            value = "No" if match else "Yes"
            all_data.append(["Financial Assistance", value, filename, page_index])

            # === Location ===
            match = re.search(r"Location\s*\[.*?[Xx].*?\]\s*([A-Za-z0-9 ]+)", text)
            value = match.group(1).strip() if match else "Location not found"
            all_data.append(["Location", value, filename, page_index])

            # === Property Values ===
            match = re.search(r"Property Values.*?(?:\[\s*X\s*\]\s*([A-Za-z0-9% \-]+))", text, re.IGNORECASE | re.DOTALL)
            value = match.group(1).strip() if match else "Property Values not found"
            all_data.append(["Property Values", value, filename, page_index])

            # === Built-Up Percentage ===
            match = re.search(r"Built[- ]Up.*?[|_\[]\s*X\s*[|_\]]\s*([A-Za-z0-9%]+)", text, re.IGNORECASE)
            value = match.group(1).strip() if match else "Built-Up not found"
            all_data.append(["Built-Up", value, filename, page_index])

            # === Demand/Supply ===
            match = re.search(r"Demand/Supply.*?[|_\[]\s*X\s*[|_\]]\s*([A-Za-z0-9% ]+)", text, re.IGNORECASE)
            value = match.group(1).strip() if match else "Demand/Supply not found"
            all_data.append(["Demand/Supply", value, filename, page_index])

            # === Growth ===
            match = re.search(r"Growth.*?\[X\]\s*([A-Za-z0-9% ]+)", text, re.IGNORECASE | re.DOTALL)
            value = match.group(1).strip() if match else "Growth not found"
            all_data.append(["Growth", value, filename, page_index])

            # === Marketing Time ===
            match = re.search(r"Marketing Time\s*\[\s*X\s*\]([A-Za-z0-9 ]+)", text, re.IGNORECASE)
            value = match.group(1).strip() if match else "Marketing Time not found"
            all_data.append(["Marketing Time", value, filename, page_index])

            # === Price Range (One-Unit) ===
            match = re.search(r"\$?\s*([0-9,]+)\s*Low.*?\$?\s*([0-9,]+)\s*High", text, re.IGNORECASE | re.DOTALL)
            value = f"${match.group(1)} – ${match.group(2)}" if match else "Price Range not found"
            all_data.append(["Price Range (One-Unit)", value, filename, page_index])

            # === Dimensions ===
            match = re.search(r"Dimensions[:\s]*([\d.,]+\s*[×xX]\s*[\d.,]+)", text)
            value = match.group(1).strip() if match else "Dimensions not found"
            all_data.append(["Dimensions", value, filename, page_index])

            # === Area ===
            match = re.search(r"Area[:\s]*([\d,]+)\s*SqFt", text)
            value = match.group(1).strip() if match else "Area not found"
            all_data.append(["Area", value, filename, page_index])

            # === Shape ===
            match = re.search(r"Shape[:\s]*([A-Za-z/]+)", text)
            value = match.group(1).strip() if match else "Shape not found"
            all_data.append(["Shape", value, filename, page_index])

            # === View ===
            match = re.search(r"View[:\s]*([A-Za-z/]+)", text)
            value = match.group(1).strip() if match else "View not found"
            all_data.append(["View", value, filename, page_index])

            # === Zoning Compliance ===
            match = re.search(r"Zoning Compliance.*?([A-Za-z ]+(?:\([^)]+\))?)", text, re.IGNORECASE | re.DOTALL)
            value = match.group(1).strip() if match else "Zoning Compliance not found"
            all_data.append(["Zoning Compliance", value, filename, page_index])

            # === Utilities ===
            match = re.search(r"Utilities[:\s]*([A-Za-z, ]+)", text)
            value = match.group(1).strip() if match else "Utilities not found"
            all_data.append(["Utilities", value, filename, page_index])

# === Extraction function for Fee Worksheet ===
def extract_fee_worksheet_data(doc, filename, all_data):
    for page_index in range(len(doc)):
        text = extract_text(doc[page_index])
        

        if page_index == 0:  # Fee Worksheet is usually first page

            # Loan Amount
            match = re.search(r"Total Loan Amount[:\s]*\$?\s*([\d,]+)", text, re.IGNORECASE)
            value = "$" + match.group(1) if match else "Loan Amount not found"
            all_data.append(["Loan Amount", value, filename, page_index])
            

            # Interest Rate
            match = re.search(r"Interest Rate[:\s]*([\d\.%]+)", text, re.IGNORECASE)
            value = match.group(1) if match else "Interest Rate not found"
            all_data.append(["Interest Rate", value, filename, page_index])
            

            # Loan Term
            match = re.search(r"Term/Due In[:\s]*(\d+)", text, re.IGNORECASE)
            value = match.group(1) + " months" if match else "Loan Term not found"
            all_data.append(["Loan Term", value, filename, page_index])
            

            # Borrower(s)
            match = re.search(r"Applicants[:\s]+(.+?)\s+Application", text, re.IGNORECASE)
            value = match.group(1).strip() if match else "Borrower not found"
            all_data.append(["Borrower", value, filename, page_index])
           

            # Origination Fee (Underwriting Fee)
            match = re.search(r"Underwriting Fee.*?\$[\s]*([\d,]+\.\d{2})", text, re.IGNORECASE | re.DOTALL)
            value = "$" + match.group(1) if match else "Origination Fee not found"
            all_data.append(["Origination Fee", value, filename, page_index])
           

            # Title Fee (Lender's Title Insurance)
            match = re.search(r"Lender'?s Title Insurance.*?\$[\s]*([\d,]+\.\d{2})", text, re.IGNORECASE | re.DOTALL)
            value = "$" + match.group(1) if match else "Title Fee not found"
            all_data.append(["Title Fee", value, filename, page_index])
           

            # Recording Fee (Mortgage Recording Charge)
            match = re.search(r"Mortgage Recording Charge.*?\$[\s]*([\d,]+\.\d{2})", text, re.IGNORECASE | re.DOTALL)
            value = "$" + match.group(1) if match else "Recording Fee not found"
            all_data.append(["Recording Fee", value, filename, page_index])
            

            # Total Fees (Funds Needed to Close)
            match = re.search(r"Total Estimated Funds needed to close\s*[:\s]*\$?\s*([\d,\.]+)", text, re.IGNORECASE)
            value = "$" + match.group(1) if match else "Total Fees not found"
            all_data.append(["Total Fees", value, filename, page_index])
            
# === Extraction function for Final 1009 ===
def extract_final_1009_data(doc, filename, all_data):
    for page_index in range(len(doc)):
        # --- Extract OCR text ---
        ocr_text = extract_text(doc[page_index])  # Your OCR function
        # --- Clean OCR text ---
        text_clean = re.sub(r'\s+', ' ', ocr_text.replace('\n', ' ').replace('\r', ' ')).strip()
        if page_index == 0:  # Only process page 0
            print(text_clean)
            # --- Borrower Name ---
            match = re.search(r"Borrower\s+([A-Za-z\s\.\-']+)", text_clean, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                all_data.append(["Borrower Name", value, filename, page_index + 1])


# === Function to print extracted data in terminal (only Field + Value) ===
def print_extracted_data(all_data):
    if not all_data:
        print("\nNo structured data extracted.")
        return
    print("\n=== Extracted Data ===")
    for field, value, _, _ in all_data:  # ignore filename & page_num
        print(f"{field}: {value}")

# === Main Processing ===
all_data = []

for filename in os.listdir(folder_path):
    if filename.lower().endswith(".pdf"):
        filepath = os.path.join(folder_path, filename)
        doc = fitz.open(filepath)

        # Detect document type
        doc_type = detect_document_type(doc)
        print(f"\nProcessing {filename} as {doc_type} (Pages: {len(doc)})")

        # Run extraction if Loan Estimate
        if doc_type == "Loan Estimate":
            extract_loan_estimate_data(doc, filename, all_data)
        elif doc_type=="Closing Disclosure":
            extract_closing_disclosure_data(doc,filename,all_data)
        elif doc_type == "Appraisal Report":
            extract_appraisal_data(doc, filename, all_data)
        elif doc_type == "Fee Worksheet":
            extract_fee_worksheet_data(doc, filename, all_data)
        elif doc_type == "Final 1009":
            extract_final_1009_data(doc, filename, all_data)

ALL_FIELDS_SNAKE = {
    "Property Address": "property_address",
    "Tax Year": "tax_year",
    "Census Tract": "census_tract",
    "Property Rights Appraised": "property_rights_appraised",
    "Neighborhood Name": "neighborhood_name",
    "Assignment Type": "assignment_type",
    "Currently Offered for Sale": "currently_offered_for_sale",
    "Data Source": "data_source",
    "List Date": "list_date",
    "Seller is Owner of Record": "seller_is_owner_of_record",
    "Financial Assistance": "financial_assistance",
    "Location": "location",
    "Property Values": "property_values",
    "Built-Up": "built_up",
    "Demand/Supply": "demand_supply",
    "Growth": "growth",
    "Marketing Time": "marketing_time",
    "Price Range (One-Unit)": "price_range_one_unit",
    "Dimensions": "dimensions",
    "Area": "area",
    "Shape": "shape",
    "View": "view",
    "Zoning Compliance": "zoning_compliance",
    "Utilities": "utilities",
    "Loan Amount": "loan_amount",
    "Interest Rate": "interest_rate",
    "Product": "product",
    "Purpose": "purpose",
    "Loan Term": "loan_term",
    "Borrower": "borrower",
    "Origination Charges": "origination_charges",
    "Services Borrower Did Shop For": "services_borrower_did_shop_for",
    "Initial Escrow Payment at Closing": "initial_escrow_payment_at_closing",
    "Total Other Costs": "total_other_costs",
    "Total Payoffs and Payments": "total_payoffs_and_payments",
    "Initial Escrow Payment": "initial_escrow_payment",
    "Origination Fee": "origination_fee",
    "Title Fee": "title_fee",
    "Recording Fee": "recording_fee",
    "Total Fees": "total_fees",
    "Borrower Name": "borrower_name",
    "Property": "property_field",
    "Sale Price": "sale_price",
    "Loan Type": "loan_type",
    "Rate Lock": "rate_lock",
    "Estimated Closing Costs": "estimated_closing_costs",
    "Services You Cannot Shop For": "services_you_cannot_shop_for",
    "Services You Can Shop For": "services_you_can_shop_for",
    "Total Closing Costs": "total_closing_costs",
    "Estimated Cash to Close": "estimated_cash_to_close",
    "Lender Name": "lender_name",
    "Loan Officer Name": "loan_officer_name",
    "Loan Officer Email": "loan_officer_email",
    "Loan Officer Phone": "loan_officer_phone",
    "Date Issued": "date_issued"
}


# === Save extracted data to JSON (flat per page, with nulls) ===
if all_data:
    output_json = "extracted_all_pdfs.json"
    grouped = {}

    for field, value, filename, page_num in all_data:
        key = (filename, page_num)
        if key not in grouped:
            filepath = os.path.join(folder_path, filename)
            doc = fitz.open(filepath)
            doc_type = detect_document_type(doc)

            # Initialize a page record with all snake_case fields = None
            grouped[key] = {
                "filename": filename,
                "document_type": doc_type,
                "page_number": page_num,
                **{v: None for v in ALL_FIELDS_SNAKE.values()}
            }

        # Only overwrite if field exists in mapping
        if field in ALL_FIELDS_SNAKE:
            grouped[key][ALL_FIELDS_SNAKE[field]] = value

    structured_output = list(grouped.values())

    with open("extracted_all_pdfs.json", "w", encoding="utf-8") as f:
        json.dump(structured_output, f, indent=4, ensure_ascii=False)

    print("\nData saved to extracted_all_pdfs.json")
