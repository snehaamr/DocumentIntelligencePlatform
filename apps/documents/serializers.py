from rest_framework import serializers

from .models import Document


class DocumentUploadSerializer(serializers.ModelSerializer):

    class Meta:

        model = Document

        fields = [
            "original_filename",
            "uploaded_file",
            "mime_type",
            "file_size",
        ]


class DocumentSerializer(serializers.ModelSerializer):

    class Meta:

        model = Document

        fields = [
            "id",
            "original_filename",
            "uploaded_file",
            "mime_type",
            "file_size",
            "status",
            "document_type",
            "summary",
            "confidence_score",
            "extracted_text",
            "ai_response",
            "metadata",
            "error_message",
            "created_at",
            "updated_at",
        ]