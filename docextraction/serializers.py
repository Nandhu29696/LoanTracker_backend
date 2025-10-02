from rest_framework import serializers
from .models import UploadedFile, LoanDocument

class DocumentUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False
    )

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = "__all__"


class LoanDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanDocument
        fields = "__all__" 