import uuid

from django.db import models


class Document(models.Model):

    STATUS_CHOICES = [
        ("UPLOADED", "UPLOADED"),
        ("PROCESSING", "PROCESSING"),
        ("PROCESSED", "PROCESSED"),
        ("FAILED", "FAILED"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    original_filename = models.CharField(
        max_length=255
    )

    uploaded_file = models.FileField(
        upload_to="documents/"
    )

    mime_type = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    file_size = models.IntegerField(
        null=True,
        blank=True
    )

    extracted_text = models.TextField(
        null=True,
        blank=True
    )

    ai_response = models.JSONField(
        null=True,
        blank=True
    )

    document_type = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    summary = models.TextField(
        null=True,
        blank=True
    )

    confidence_score = models.FloatField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="UPLOADED"
    )

    error_message = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )


    def __str__(self):
        return self.original_filename