import fitz
import re
import pytesseract
from PIL import Image
import io

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

# ----------------- Helpers -----------------
def extract_text(page):
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img)

def extract_text_layer(page):
    return page.get_text("text")

def get_footer_text(doc):
    footer_text = ""
    for page in doc:
        blocks = page.get_text("blocks")
        page_height = page.rect.height
        for block in blocks:
            x0, y0, x1, y1, text, *_ = block
            if y0 > page_height * 0.85:
                footer_text += " " + text
    return footer_text.strip()

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


# ----------------- Extraction Functions -----------------
# Place all your original extraction functions here
# Example for Loan Estimate
def extract_loan_estimate_data(doc, filename, all_data):
    for page_index in range(len(doc)):
        text = extract_text(doc[page_index])
        if page_index == 1:
            match = re.search(r"Loan Amount\s+\$?([\d,]+)", text)
            if match:
                value = "$" + match.group(1).strip()
                all_data.append(["Loan Amount", value, filename, page_index + 1])
        # Add all other fields extraction here exactly like your original script

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


# ----------------- Structuring Output -----------------
def structure_extracted_data(all_data, doc_type_per_file=None):
    """
    Converts raw extracted list [field, value, filename, page_num] into a structured JSON.
    All fields from ALL_FIELDS are included, missing ones are None.
    """
    structured = {}
    print(all_data)
    for field, value, filename, page_num in all_data:
        key = (filename, page_num)
        if key not in structured:
            # Start with all fields = None
            # Initialize a page record with all snake_case fields = None
            structured[key] = {
                "filename": filename,
                "document_type": doc_type_per_file.get(filename) if doc_type_per_file else "Unknown",
                "page_number": page_num,
                **{v: None for v in ALL_FIELDS_SNAKE.values()}
            }

        # Only overwrite if field exists in mapping
        if field in ALL_FIELDS_SNAKE:
            structured[key][ALL_FIELDS_SNAKE[field]] = value
            
    return list(structured.values())
 