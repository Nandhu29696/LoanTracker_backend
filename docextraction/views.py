from rest_framework import generics, permissions
from .models import Docfile
from .serializers import DocumentSerializer
from .utils import process_document

class DocumentUploadView(generics.CreateAPIView):

    permission_classes = [permissions.IsAuthenticated]
    queryset = Docfile.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        document = serializer.save(user=self.request.user)
        process_document(document)  # Run extraction pipeline
