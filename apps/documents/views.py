from rest_framework import status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from services.document_service import DocumentService

from .serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
)


class DocumentViewSet(viewsets.ViewSet):

    parser_classes = [MultiPartParser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = DocumentService()

    def create(self, request):

        serializer = DocumentUploadSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        document = self.service.upload_document(
            serializer.validated_data["file"]
        )

        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):

        document = self.service.get_document(pk)

        serializer = DocumentSerializer(document)

        return Response(serializer.data)

    def list(self, request):

        documents = self.service.list_documents(
            status=request.query_params.get("status"),
            document_type=request.query_params.get("document_type"),
            search=request.query_params.get("search"),
        )

        paginator = PageNumberPagination()

        page = paginator.paginate_queryset(
            documents,
            request,
        )

        serializer = DocumentSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )