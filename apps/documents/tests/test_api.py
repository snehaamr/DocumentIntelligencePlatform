from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents.models import (
    Document,
    DocumentProcessingLog,
)


User = get_user_model()


class DocumentApiTests(APITestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="password123",
        )

        self.other_user = User.objects.create_user(
            username="other",
            password="password123",
        )

        self.client.force_authenticate(
            user=self.owner
        )

    def create_document(
        self,
        owner=None,
        status_value="PROCESSED",
        filename="sample.pdf",
    ):
        uploaded_file = SimpleUploadedFile(
            filename,
            b"sample document content",
            content_type="application/pdf",
        )

        return Document.objects.create(
            owner=owner or self.owner,
            original_filename=filename,
            uploaded_file=uploaded_file,
            mime_type="application/pdf",
            file_size=len(
                b"sample document content"
            ),
            status=status_value,
        )

    def test_unauthenticated_list_is_rejected(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            "/api/documents/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_list_only_returns_owners_documents(self):
        self.create_document(
            owner=self.owner,
            filename="mine.pdf",
        )

        self.create_document(
            owner=self.other_user,
            filename="theirs.pdf",
        )

        response = self.client.get(
            "/api/documents/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        results = response.data.get(
            "results",
            response.data,
        )

        filenames = [
            item["original_filename"]
            for item in results
        ]

        self.assertIn(
            "mine.pdf",
            filenames,
        )

        self.assertNotIn(
            "theirs.pdf",
            filenames,
        )

    def test_history_endpoint_returns_processing_logs(self):
        document = self.create_document()

        DocumentProcessingLog.objects.create(
            document=document,
            status=(
                DocumentProcessingLog
                .Status
                .SUCCEEDED
            ),
            duration_ms=7772,
        )

        response = self.client.get(
            (
                f"/api/documents/"
                f"{document.id}/history/"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["duration_ms"],
            7772,
        )

        self.assertEqual(
            response.data[0]["status"],
            "SUCCEEDED",
        )

    def test_history_of_other_users_document_returns_404(
        self,
    ):
        document = self.create_document(
            owner=self.other_user
        )

        response = self.client.get(
            (
                f"/api/documents/"
                f"{document.id}/history/"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_retry_processed_document_returns_conflict(
        self,
    ):
        document = self.create_document(
            status_value="PROCESSED"
        )

        response = self.client.post(
            (
                f"/api/documents/"
                f"{document.id}/retry/"
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )

    @patch(
        "apps.documents.tasks."
        "process_document_task.delay"
    )
    def test_retry_failed_document_is_accepted(
        self,
        mock_delay,
    ):
        document = self.create_document(
            status_value="FAILED"
        )

        with self.captureOnCommitCallbacks(
            execute=True
        ):
            response = self.client.post(
                (
                    f"/api/documents/"
                    f"{document.id}/retry/"
                ),
                {},
                format="json",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED,
        )

        document.refresh_from_db()

        self.assertEqual(
            document.status,
            "UPLOADED",
        )

        mock_delay.assert_called_once_with(
            str(document.id)
        )

    def test_retry_other_users_document_returns_404(
        self,
    ):
        document = self.create_document(
            owner=self.other_user,
            status_value="FAILED",
        )

        response = self.client.post(
            (
                f"/api/documents/"
                f"{document.id}/retry/"
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_filter_documents_by_status(self):
        self.create_document(
            status_value="PROCESSED",
            filename="processed.pdf",
        )

        self.create_document(
            status_value="FAILED",
            filename="failed.pdf",
        )

        response = self.client.get(
            "/api/documents/?status=FAILED"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        results = response.data.get(
            "results",
            response.data,
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["original_filename"],
            "failed.pdf",
        )