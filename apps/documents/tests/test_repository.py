from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.documents.models import Document
from repositories.document_repository import DocumentRepository


User = get_user_model()


class DocumentRepositoryTests(TestCase):

    def setUp(self):
        self.repository = DocumentRepository()

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
        owner,
        filename="sample.pdf",
        status="UPLOADED",
        document_type=None,
        confidence_score=None,
        summary=None,
    ):
        uploaded_file = SimpleUploadedFile(
            filename,
            b"sample document content",
            content_type="application/pdf",
        )

        return Document.objects.create(
            owner=owner,
            original_filename=filename,
            uploaded_file=uploaded_file,
            mime_type="application/pdf",
            file_size=len(
                b"sample document content"
            ),
            status=status,
            document_type=document_type,
            confidence_score=confidence_score,
            summary=summary,
        )

    def test_get_by_id_returns_document(self):
        document = self.create_document(
            owner=self.owner
        )

        result = self.repository.get_by_id(
            document.id
        )

        self.assertEqual(
            result,
            document,
        )

    def test_get_by_id_for_owner_returns_document(self):
        document = self.create_document(
            owner=self.owner
        )

        result = (
            self.repository
            .get_by_id_for_owner(
                document_id=document.id,
                owner=self.owner,
            )
        )

        self.assertEqual(
            result,
            document,
        )

    def test_get_by_id_for_owner_hides_other_users_document(
        self,
    ):
        document = self.create_document(
            owner=self.owner
        )

        result = (
            self.repository
            .get_by_id_for_owner(
                document_id=document.id,
                owner=self.other_user,
            )
        )

        self.assertIsNone(result)

    def test_filter_documents_is_scoped_to_owner(self):
        self.create_document(
            owner=self.owner,
            filename="mine.pdf",
        )

        self.create_document(
            owner=self.other_user,
            filename="theirs.pdf",
        )

        results = (
            self.repository
            .filter_documents(
                owner=self.owner
            )
        )

        self.assertEqual(
            results.count(),
            1,
        )

        self.assertEqual(
            results.first().original_filename,
            "mine.pdf",
        )

    def test_filter_documents_by_status(self):
        self.create_document(
            owner=self.owner,
            filename="processed.pdf",
            status="PROCESSED",
        )

        self.create_document(
            owner=self.owner,
            filename="failed.pdf",
            status="FAILED",
        )

        results = (
            self.repository
            .filter_documents(
                owner=self.owner,
                status="FAILED",
            )
        )

        self.assertEqual(
            results.count(),
            1,
        )

        self.assertEqual(
            results.first().status,
            "FAILED",
        )

    def test_filter_documents_by_document_type(self):
        self.create_document(
            owner=self.owner,
            filename="bill.pdf",
            document_type="Utility Bill",
        )

        self.create_document(
            owner=self.owner,
            filename="invoice.pdf",
            document_type="Invoice",
        )

        results = (
            self.repository
            .filter_documents(
                owner=self.owner,
                document_type="Utility Bill",
            )
        )

        self.assertEqual(
            results.count(),
            1,
        )

        self.assertEqual(
            results.first().document_type,
            "Utility Bill",
        )

    def test_filter_documents_by_min_confidence(self):
        self.create_document(
            owner=self.owner,
            filename="high.pdf",
            confidence_score=0.95,
        )

        self.create_document(
            owner=self.owner,
            filename="low.pdf",
            confidence_score=0.50,
        )

        results = (
            self.repository
            .filter_documents(
                owner=self.owner,
                min_confidence=0.90,
            )
        )

        self.assertEqual(
            results.count(),
            1,
        )

        self.assertEqual(
            results.first().original_filename,
            "high.pdf",
        )

    def test_search_documents_by_filename_or_summary(self):
        self.create_document(
            owner=self.owner,
            filename="energy_bill.pdf",
            summary="Monthly utility statement",
        )

        self.create_document(
            owner=self.owner,
            filename="contract.pdf",
            summary="Employment agreement",
        )

        results = (
            self.repository
            .filter_documents(
                owner=self.owner,
                search="utility",
            )
        )

        self.assertEqual(
            results.count(),
            1,
        )

        self.assertEqual(
            results.first().original_filename,
            "energy_bill.pdf",
        )