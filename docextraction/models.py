from django.db import models
from django.contrib.auth.models import User

# -------------------------------
# Table to store uploaded files
# -------------------------------
class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_files")
    filename = models.CharField(max_length=255)
    filetype = models.CharField(max_length=50)
    filesize = models.PositiveBigIntegerField()  # must be numeric
    file = models.FileField(upload_to="documents/")  # stores file path
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename

# -------------------------------
# Table to store extracted loan document info
# -------------------------------
class LoanDocument(models.Model):
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name="loan_documents")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    page_number = models.IntegerField(default=0)
    document_type = models.CharField(max_length=255, blank=True, null=True)

    # All extracted fields
    property_address = models.TextField(blank=True, null=True)
    tax_year = models.CharField(max_length=10, blank=True, null=True)
    census_tract = models.CharField(max_length=50, blank=True, null=True)
    property_rights_appraised = models.CharField(max_length=50, blank=True, null=True)
    neighborhood_name = models.TextField(blank=True, null=True)
    assignment_type = models.CharField(max_length=255, blank=True, null=True)
    currently_offered_for_sale = models.CharField(max_length=10, blank=True, null=True)
    data_source = models.CharField(max_length=255, blank=True, null=True)
    list_date = models.CharField(max_length=50, blank=True, null=True)
    seller_is_owner_of_record = models.CharField(max_length=10, blank=True, null=True)
    financial_assistance = models.CharField(max_length=10, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    property_values = models.CharField(max_length=255, blank=True, null=True)
    built_up = models.CharField(max_length=50, blank=True, null=True)
    demand_supply = models.CharField(max_length=50, blank=True, null=True)
    growth = models.CharField(max_length=50, blank=True, null=True)
    marketing_time = models.CharField(max_length=255, blank=True, null=True)
    price_range_one_unit = models.CharField(max_length=255, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=50, blank=True, null=True)
    shape = models.CharField(max_length=50, blank=True, null=True)
    view = models.CharField(max_length=50, blank=True, null=True)
    zoning_compliance = models.CharField(max_length=255, blank=True, null=True)
    utilities = models.CharField(max_length=255, blank=True, null=True)

    # Loan-specific fields
    loan_amount = models.CharField(max_length=50, blank=True, null=True)
    interest_rate = models.CharField(max_length=50, blank=True, null=True)
    product = models.CharField(max_length=255, blank=True, null=True)
    purpose = models.CharField(max_length=50, blank=True, null=True)
    loan_term = models.CharField(max_length=50, blank=True, null=True)
    borrower = models.CharField(max_length=255, blank=True, null=True)
    origination_charges = models.CharField(max_length=50, blank=True, null=True)
    services_borrower_did_shop_for = models.CharField(max_length=255, blank=True, null=True)
    initial_escrow_payment_at_closing = models.CharField(max_length=50, blank=True, null=True)
    total_other_costs = models.CharField(max_length=50, blank=True, null=True)
    total_payoffs_and_payments = models.CharField(max_length=50, blank=True, null=True)
    initial_escrow_payment = models.CharField(max_length=50, blank=True, null=True)
    origination_fee = models.CharField(max_length=50, blank=True, null=True)
    title_fee = models.CharField(max_length=50, blank=True, null=True)
    recording_fee = models.CharField(max_length=50, blank=True, null=True)
    total_fees = models.CharField(max_length=50, blank=True, null=True)
    borrower_name = models.CharField(max_length=255, blank=True, null=True)
    property_field = models.TextField(blank=True, null=True)  # avoid using 'property' keyword
    sale_price = models.CharField(max_length=50, blank=True, null=True)
    loan_type = models.CharField(max_length=50, blank=True, null=True)
    rate_lock = models.CharField(max_length=50, blank=True, null=True)
    estimated_closing_costs = models.CharField(max_length=50, blank=True, null=True)
    services_you_cannot_shop_for = models.CharField(max_length=255, blank=True, null=True)
    services_you_can_shop_for = models.CharField(max_length=255, blank=True, null=True)
    total_closing_costs = models.CharField(max_length=50, blank=True, null=True)
    estimated_cash_to_close = models.CharField(max_length=50, blank=True, null=True)
    lender_name = models.CharField(max_length=255, blank=True, null=True)
    loan_officer_name = models.CharField(max_length=255, blank=True, null=True)
    loan_officer_email = models.CharField(max_length=255, blank=True, null=True)
    loan_officer_phone = models.CharField(max_length=50, blank=True, null=True)
    date_issued = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.document_type} - {self.uploaded_file.filename} - Page {self.page_number}"
