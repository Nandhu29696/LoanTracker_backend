from django.urls import path
from .views import PDFUploadAPIView, LoanListAPIView

urlpatterns = [
    path("upload/", PDFUploadAPIView.as_view(), name="document-upload"),
    path('loans/fetchLoans/', LoanListAPIView.as_view(), name='loan-list'),

]
 