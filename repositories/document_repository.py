from django.db.models import Q

from apps.documents.models import Document


class DocumentRepository:

    def create(
        self,
        original_filename,
        uploaded_file,
        mime_type,
        file_size,
        owner=None,
    ):
        create_data = {
            "original_filename": original_filename,
            "uploaded_file": uploaded_file,
            "mime_type": mime_type,
            "file_size": file_size,
        }

        if owner is not None:
            create_data["owner"] = owner

        return Document.objects.create(
            **create_data
        )

    def get_by_id(
        self,
        document_id,
    ):
        return Document.objects.get(
            id=document_id
        )

    def get_by_id_for_owner(
        self,
        document_id,
        owner,
    ):
        return (
            Document.objects
            .filter(
                id=document_id,
                owner=owner,
            )
            .first()
        )

    def get_by_id_for_update(
        self,
        document_id,
        owner,
    ):
        """
        Retrieve and lock a document for an update.

        This method must be called inside
        transaction.atomic().
        """

        return (
            Document.objects
            .select_for_update()
            .filter(
                id=document_id,
                owner=owner,
            )
            .first()
        )

    def save(
        self,
        document,
        update_fields=None,
    ):
        document.save(
            update_fields=update_fields
        )

        return document

    def filter_documents(
        self,
        owner=None,
        status=None,
        document_type=None,
        search=None,
        min_confidence=None,
    ):
        queryset = Document.objects.all()

        if owner is not None:
            queryset = queryset.filter(
                owner=owner
            )

        if status:
            queryset = queryset.filter(
                status=status
            )

        if document_type:
            queryset = queryset.filter(
                document_type=document_type
            )

        if min_confidence is not None:
            queryset = queryset.filter(
                confidence_score__gte=min_confidence
            )

        if search:
            queryset = queryset.filter(
                Q(
                    original_filename__icontains=search
                )
                |
                Q(
                    summary__icontains=search
                )
            )

        return queryset.order_by(
            "-created_at"
        )