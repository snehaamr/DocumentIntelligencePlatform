from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.documents.models import (
    Document,
    DocumentProcessingLog,
)
from services.document_service import DocumentService
from services.exceptions import (
    DocumentNotFoundError,
    DocumentRetryNotAllowedError,
)


User = get_user_model()


class DocumentServiceTests(TestCase):

    def setUp(self):
        self.service = DocumentService()

        self.owner = User.objects.create_user(
            username="owner",
            password="password123",
        )

        self.other_user = User.objects.create_user(
            username="other",
            password="password123",
        )

    def create_document(
        self,
        owner=None,
        status="FAILED",
    ):
        uploaded_file = SimpleUploadedFile(
            "sample.pdf",
            b"sample document content",
            content_type="application/pdf",
        )

        return Document.objects.create(
            owner=owner or self.owner,
            original_filename="sample.pdf",
            uploaded_file=uploaded_file,
            mime_type="application/pdf",
            file_size=len(
                b"sample document content"
            ),
            status=status,
        )

    def test_get_processing_history(self):
        document = self.create_document(
            status="PROCESSED"
        )

        DocumentProcessingLog.objects.create(
            document=document,
            status=(
                DocumentProcessingLog
                .Status
                .SUCCEEDED
            ),
            duration_ms=7772,
        )

        history = (
            self.service
            .get_processing_history(
                document_id=document.id,
                owner=self.owner,
            )
        )

        self.assertEqual(
            history.count(),
            1,
        )

        self.assertEqual(
            history.first().duration_ms,
            7772,
        )

    def test_processing_history_hides_other_users_document(
        self,
    ):
        document = self.create_document(
            owner=self.other_user,
            status="PROCESSED",
        )

        with self.assertRaises(
            DocumentNotFoundError
        ):
            self.service.get_processing_history(
                document_id=document.id,
                owner=self.owner,
            )

    @patch(
        "apps.documents.tasks."
        "process_document_task.delay"
    )
    def test_retry_failed_document(
        self,
        mock_delay,
    ):
        document = self.create_document(
            status="FAILED"
        )

        with self.captureOnCommitCallbacks(
            execute=True
        ):
            result = self.service.retry_document(
                document_id=document.id,
                owner=self.owner,
            )

        result.refresh_from_db()

        self.assertEqual(
            result.status,
            "UPLOADED",
        )

        self.assertEqual(
            result.error_message,
            "",
        )

        mock_delay.assert_called_once_with(
            str(document.id)
        )

    def test_retry_processed_document_is_rejected(self):
        document = self.create_document(
            status="PROCESSED"
        )

        with self.assertRaises(
            DocumentRetryNotAllowedError
        ):
            self.service.retry_document(
                document_id=document.id,
                owner=self.owner,
            )

    def test_retry_other_users_document_is_hidden(self):
        document = self.create_document(
            owner=self.other_user,
            status="FAILED",
        )

        with self.assertRaises(
            DocumentNotFoundError
        ):
            self.service.retry_document(
                document_id=document.id,
                owner=self.owner,
            )

    def test_list_documents_is_scoped_to_owner(self):
        self.create_document(
            owner=self.owner,
            status="PROCESSED",
        )

        self.create_document(
            owner=self.other_user,
            status="PROCESSED",
        )

        results = self.service.list_documents(
            owner=self.owner
        )

        self.assertEqual(
            results.count(),
            1,
        )