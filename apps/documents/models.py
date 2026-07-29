import uuid

from django.db import models
from django.contrib.auth.models import User



class Document(models.Model):

    STATUS_CHOICES = [
        ("UPLOADED", "UPLOADED"),
        ("EXTRACTING", "EXTRACTING"),
        ("ANALYZING", "ANALYZING"),
        ("PROCESSED", "PROCESSED"),
        ("FAILED", "FAILED"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    owner = models.ForeignKey(
   	    User,
        on_delete=models.CASCADE,
        related_name="documents"
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

    # Raw response returned from AI service
    ai_response = models.JSONField(
        null=True,
        blank=True
    )

    # Structured metadata extracted from document
    metadata = models.JSONField(
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
        
class DocumentProcessingLog(models.Model):

    class Status(models.TextChoices):
        STARTED = "STARTED", "Started"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="processing_logs",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.STARTED,
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    duration_ms = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    model_used = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    tokens_used = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "document_processing_logs"

        ordering = [
            "-started_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "document",
                    "status",
                ],
                name="doc_log_doc_status_idx",
            ),
            models.Index(
                fields=[
                    "status",
                    "started_at",
                ],
                name="doc_log_status_time_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.document.original_filename} "
            f"- {self.status} "
            f"- {self.started_at}"
        )        