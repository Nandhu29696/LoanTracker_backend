from rest_framework import serializers
from .models import Docfile

class DocumentUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False
    )

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Docfile
        fields = "__all__"
