from django.db import models
from django.contrib.auth.models import User

class Docfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="docfile")
    file = models.FileField(upload_to="documents/")
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20)
    extracted_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} uploaded by {self.user.username}"


class ExtractedField(models.Model):
    document = models.OneToOneField(Docfile, related_name="extracted_data", on_delete=models.CASCADE)

    # Example fields for Loan Estimate
    loan_amount = models.CharField(max_length=255, null=True, blank=True)
    date_issued = models.CharField(max_length=50, null=True, blank=True)
    borrower_name = models.CharField(max_length=255, null=True, blank=True)
    lender_name = models.CharField(max_length=255, null=True, blank=True)
    loan_term = models.CharField(max_length=50, null=True, blank=True)
    interest_rate = models.CharField(max_length=50, null=True, blank=True)
    apr = models.CharField(max_length=50, null=True, blank=True)

    # Example fields for Closing Disclosure
    closing_date = models.CharField(max_length=50, null=True, blank=True)
    disbursement_date = models.CharField(max_length=50, null=True, blank=True)
    sales_price = models.CharField(max_length=50, null=True, blank=True)

    # Catch-all for misc
    document_type = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Extracted fields for {self.document.file.name}"
