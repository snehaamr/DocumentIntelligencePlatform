from django.db import transaction

from repositories.document_repository import DocumentRepository
from services.ai_document_service import AIDocumentService
from services.exceptions import (
    DocumentNotFoundError,
    DocumentRetryNotAllowedError,
)
from services.extraction_service import ExtractionService


class DocumentService:

    def __init__(
        self,
        repository=None,
        extraction_service=None,
        ai_document_service=None,
    ):
        self.repository = (
            repository
            or DocumentRepository()
        )

        self.extraction_service = (
            extraction_service
            or ExtractionService()
        )

        self.ai_document_service = (
            ai_document_service
            or AIDocumentService()
        )

    def upload_document(
        self,
        uploaded_file,
        owner=None,
    ):
        document = self.repository.create(
            original_filename=uploaded_file.name,
            uploaded_file=uploaded_file,
            mime_type=uploaded_file.content_type,
            file_size=uploaded_file.size,
            owner=owner,
        )

        return document

    def process_document(
        self,
        document_id,
    ):
        document = self.repository.get_by_id(
            document_id
        )

        document.status = "PROCESSING"
        document.error_message = ""

        self.repository.save(
            document
        )

        try:
            extracted_text = (
                self.extraction_service.extract(
                    document.uploaded_file.path
                )
            )

            ai_result = (
                self.ai_document_service.analyze(
                    extracted_text
                )
            )

            document.extracted_text = (
                extracted_text
            )

            document.ai_response = (
                ai_result.model_dump()
            )

            document.document_type = (
                ai_result.document_type
            )

            document.summary = (
                ai_result.summary
            )

            document.confidence_score = (
                ai_result.confidence_score
            )

            document.status = "PROCESSED"
            document.error_message = ""

            self.repository.save(
                document
            )

            return document

        except Exception as exc:
            document.status = "FAILED"
            document.error_message = str(exc)

            self.repository.save(
                document
            )

            raise

    def get_document(
        self,
        document_id,
    ):
        return self.repository.get_by_id(
            document_id
        )

    def list_documents(
        self,
        owner=None,
        status=None,
        document_type=None,
        search=None,
        min_confidence=None,
    ):
        return self.repository.filter_documents(
            owner=owner,
            status=status,
            document_type=document_type,
            search=search,
            min_confidence=min_confidence,
        )

    def retry_document(
        self,
        document_id,
        owner,
    ):
        """
        Retry a failed document-processing attempt.

        The document row is locked while its status is
        changed. The Celery task is queued only after the
        database transaction commits successfully.
        """

        with transaction.atomic():
            document = (
                self.repository
                .get_by_id_for_update(
                    document_id=document_id,
                    owner=owner,
                )
            )

            if document is None:
                raise DocumentNotFoundError(
                    "Document not found."
                )

            if document.status != "FAILED":
                raise DocumentRetryNotAllowedError(
                    "Only failed documents can be retried."
                )

            document.status = "UPLOADED"
            document.error_message = ""

            self.repository.save(
                document=document,
                update_fields=[
                    "status",
                    "error_message",
                ],
            )

            transaction.on_commit(
                lambda document_id=str(document.id):
                    self._queue_document_processing(
                        document_id
                    )
            )

        return document
        
        
    def get_processing_history(
        self,
        document_id,
        owner,
    ):
        document = (
            self.repository
            .get_by_id_for_owner(
                document_id=document_id,
                owner=owner,
            )
        )

        if document is None:
            raise DocumentNotFoundError(
                "Document not found."
            )

        return document.processing_logs.all()    

    def _queue_document_processing(
        self,
        document_id,
    ):
        """
        Queue document processing without causing
        a circular import during application startup.
        """

        from apps.documents.tasks import (
            process_document_task,
        )

        process_document_task.delay(
            document_id
        )