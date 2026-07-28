from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from services.document_service import DocumentService
from services.tasks import process_document_task

from .serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
)


class DocumentUploadView(APIView):

    service = DocumentService()

    def post(self, request):

        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document = self.service.upload_document(
            serializer.validated_data["file"]
        )

        # This line is critical
        process_document_task.delay(str(document.id))

        return Response(
            {
                "id": str(document.id),
                "status": document.status,
                "message": "Document uploaded and processing started",
            },
            status=status.HTTP_201_CREATED,
        )



class ProcessDocumentView(APIView):

    def post(self, request, document_id):

        service = DocumentService()

        document = service.process_document(
            document_id
        )

        return Response({

            "id": str(document.id),

            "status": document.status,

            "document_type":
                document.document_type,

            "summary":
                document.summary,

            "confidence":
                document.confidence_score

        })