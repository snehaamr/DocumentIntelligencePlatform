from django.db import models
import uuid


class Document(models.Model):

    STATUS_CHOICES = [
        ("UPLOADED", "Uploaded"),
        ("PROCESSING", "Processing"),
        ("PROCESSED", "Processed"),
        ("FAILED", "Failed"),
    ]

    DOCUMENT_TYPES = [
        ("INVOICE", "Invoice"),
        ("CONTRACT", "Contract"),
        ("RECEIPT", "Receipt"),
        ("PURCHASE_ORDER", "Purchase Order"),
        ("OTHER", "Other"),
    ]


    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )


    # Original uploaded file
    file = models.FileField(
        upload_to="documents/"
    )


    # Original filename for display
    filename = models.CharField(
        max_length=255
    )


    # Processing lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="UPLOADED"
    )


    # Extracted raw text from PDF/DOCX/TXT
    extracted_text = models.TextField(
        blank=True,
        null=True
    )


    # AI generated structured response
    ai_response = models.JSONField(
        blank=True,
        null=True
    )


    # AI extracted metadata
    document_type = models.CharField(
        max_length=100,
        choices=DOCUMENT_TYPES,
        blank=True,
        null=True
    )


    summary = models.TextField(
        blank=True,
        null=True
    )


    confidence_score = models.FloatField(
        blank=True,
        null=True
    )


    # Error tracking
    error_message = models.TextField(
        blank=True,
        null=True
    )


    # Audit fields
    created_at = models.DateTimeField(
        auto_now_add=True
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )


    def __str__(self):
        return self.filename