from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import transaction
from .models import UploadedFile, LoanDocument
from .serializers import LoanDocumentSerializer
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

from .utils import (
    extract_loan_estimate_data,
    extract_closing_disclosure_data,
    extract_appraisal_data,
    extract_fee_worksheet_data,
    extract_final_1009_data,
    detect_document_type,
    structure_extracted_data
)
import fitz


class PDFUploadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist("files")
        if not files:
            return Response({"error": "No files uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        all_data = []
        doc_type_per_file = {}
        user = request.user
        uploaded_files_map = {}  # Map filename -> UploadedFile object

        with transaction.atomic():
            for file in files:
                # Save uploaded file info
                uploaded_file_obj = UploadedFile.objects.create(
                    user=user,
                    filename=file.name,
                    filetype=file.content_type,
                    filesize=file.size,
                    file=file,
                    uploaded_at=timezone.now()
                )
                uploaded_files_map[file.name] = uploaded_file_obj

                file.seek(0)
                try:
                    doc = fitz.open(stream=file.read(), filetype="pdf")
                except Exception as e:
                    return Response({"error": f"Failed to open {file.name}: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

                # Detect document type
                doc_type = detect_document_type(doc)
                doc_type_per_file[file.name] = doc_type

                # Extract data
                file_data = []
                if doc_type == "Loan Estimate":
                    extract_loan_estimate_data(doc, file.name, file_data)
                elif doc_type == "Closing Disclosure":
                    extract_closing_disclosure_data(doc, file.name, file_data)
                elif doc_type == "Appraisal Report":
                    extract_appraisal_data(doc, file.name, file_data)
                elif doc_type == "Fee Worksheet":
                    extract_fee_worksheet_data(doc, file.name, file_data)
                elif doc_type == "Final 1009":
                    extract_final_1009_data(doc, file.name, file_data)

                all_data.extend(file_data)

        # Structure extracted data
        structured_output = structure_extracted_data(all_data, doc_type_per_file)

        # Prepare LoanDocument objects
        loan_documents = []
        for record in structured_output:
            record_dict = record.copy()
            filename = record_dict.pop("filename", None)
            page_number = record_dict.pop("page_number", 0)
            doc_type = record_dict.pop("document_type", "Unknown")

            uploaded_file_obj = uploaded_files_map.get(filename)
            if not uploaded_file_obj:
                # Skip if file not found
                continue

            loan_documents.append(
                LoanDocument(
                    uploaded_file=uploaded_file_obj,
                    user=user,
                    document_type=doc_type,
                    page_number=page_number,
                    **record_dict
                )
            )

        # Bulk save all LoanDocument records
        LoanDocument.objects.bulk_create(loan_documents)

        return Response(structured_output, status=status.HTTP_201_CREATED)

    
# API to list all loans
class LoanListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = LoanDocument.objects.all()
    serializer_class = LoanDocumentSerializer
    
    
