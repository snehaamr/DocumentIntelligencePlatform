import logging
from time import monotonic

from celery import shared_task
from django.utils import timezone

from apps.documents.models import (
    Document,
    DocumentProcessingLog,
)
from services.document_service import DocumentService


logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="documents.process_document",
)
def process_document_task(
    self,
    document_id,
):
    document = _get_document(
        document_id=document_id,
    )

    processing_log = (
        DocumentProcessingLog.objects.create(
            document=document,
            status=DocumentProcessingLog.Status.STARTED,
        )
    )

    start_time = monotonic()

    try:
        document.status = "PROCESSING"
        document.save(
            update_fields=[
                "status",
            ],
        )

        service = DocumentService()

        service.process_document(
            document_id=document.id,
        )

        duration_ms = _calculate_duration_ms(
            start_time=start_time,
        )

        processing_log.status = (
            DocumentProcessingLog.Status.SUCCEEDED
        )
        processing_log.completed_at = timezone.now()
        processing_log.duration_ms = duration_ms
        processing_log.error_message = ""

        processing_log.save(
            update_fields=[
                "status",
                "completed_at",
                "duration_ms",
                "error_message",
                "updated_at",
            ],
        )

        logger.info(
            "Document processing succeeded. "
            "document_id=%s task_id=%s duration_ms=%s",
            document.id,
            self.request.id,
            duration_ms,
        )

        return {
            "document_id": str(document.id),
            "processing_log_id": str(
                processing_log.id
            ),
            "status": (
                DocumentProcessingLog
                .Status
                .SUCCEEDED
            ),
            "duration_ms": duration_ms,
        }

    except Exception as exc:
        duration_ms = _calculate_duration_ms(
            start_time=start_time,
        )

        document.status = "FAILED"
        document.save(
            update_fields=[
                "status",
            ],
        )

        processing_log.status = (
            DocumentProcessingLog.Status.FAILED
        )
        processing_log.completed_at = timezone.now()
        processing_log.duration_ms = duration_ms
        processing_log.error_message = str(exc)

        processing_log.save(
            update_fields=[
                "status",
                "completed_at",
                "duration_ms",
                "error_message",
                "updated_at",
            ],
        )

        logger.exception(
            "Document processing failed. "
            "document_id=%s task_id=%s duration_ms=%s",
            document.id,
            self.request.id,
            duration_ms,
        )

        raise


def _get_document(
    document_id,
):
    try:
        return Document.objects.get(
            id=document_id,
        )

    except Document.DoesNotExist as exc:
        raise ValueError(
            f"Document with ID {document_id} "
            "does not exist."
        ) from exc


def _calculate_duration_ms(
    start_time,
):
    elapsed_seconds = (
        monotonic() - start_time
    )

    return max(
        0,
        round(elapsed_seconds * 1000),
    )