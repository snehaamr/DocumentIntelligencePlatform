from apps.documents.models import Document


class DocumentRepository:


    def create(
        self,
        original_filename,
        uploaded_file,
        mime_type,
        file_size
    ):

        return Document.objects.create(
            filename=original_filename,
            file=uploaded_file,
            mime_type=mime_type,
            file_size=file_size
        )


    def get_by_id(self, document_id):

        return Document.objects.get(
            id=document_id
        )