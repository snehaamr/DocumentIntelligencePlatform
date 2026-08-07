from rest_framework import serializers

from .models import (
    Document,
    DocumentProcessingLog,
)


class DocumentUploadSerializer(
    serializers.Serializer
):

    file = serializers.FileField()


class DocumentSerializer(
    serializers.ModelSerializer
):

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

        read_only_fields = fields


class DocumentProcessingLogSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = DocumentProcessingLog

        fields = [
            "id",
            "status",
            "started_at",
            "completed_at",
            "duration_ms",
            "model_used",
            "tokens_used",
            "error_message",
        ]

        read_only_fields = fields