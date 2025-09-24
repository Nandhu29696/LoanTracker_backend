from django.contrib import admin
from .models import Docfile, ExtractedField


@admin.register(Docfile)
class DocfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "filename", "file_type", "uploaded_at")
    search_fields = ("filename", "user__username", "file_type")
    list_filter = ("file_type", "uploaded_at")
    ordering = ("-uploaded_at",)


@admin.register(ExtractedField)
class ExtractedFieldAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "loan_amount",
        "borrower_name",
        "lender_name",
        "loan_term",
        "interest_rate",
        "apr",
        "closing_date",
        "created_at",
    )
    search_fields = ("loan_amount", "borrower_name", "lender_name", "document__filename")
    list_filter = ("document_type", "created_at")
    ordering = ("-created_at",)
