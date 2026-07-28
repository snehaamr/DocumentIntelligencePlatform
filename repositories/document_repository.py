from django.db.models import Q

from apps.documents.models import Document


class DocumentRepository:

    def create(
        self,
        original_filename,
        uploaded_file,
        mime_type,
        file_size,
    ):

        return Document.objects.create(
            original_filename=original_filename,
            uploaded_file=uploaded_file,
            mime_type=mime_type,
            file_size=file_size,
        )

    def get_by_id(
        self,
        document_id,
    ):

        return Document.objects.get(
            id=document_id
        )

    def save(
        self,
        document,
    ):

        document.save()

        return document

    def filter_documents(
        self,
        status=None,
        document_type=None,
        search=None,
    ):

        queryset = Document.objects.all()

        if status:
            queryset = queryset.filter(
                status=status
            )

        if document_type:
            queryset = queryset.filter(
                document_type=document_type
            )

        if search:
            queryset = queryset.filter(
                Q(original_filename__icontains=search)
                |
                Q(summary__icontains=search)
            )

        return queryset.order_by(
            "-created_at"
        )