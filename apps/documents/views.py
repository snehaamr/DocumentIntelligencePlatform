from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from services.document_service import DocumentService
from services.exceptions import (
    DocumentNotFoundError,
    DocumentRetryNotAllowedError,
)

from .serializers import (
    DocumentProcessingLogSerializer,
    DocumentSerializer,
    DocumentUploadSerializer,
)


class DocumentViewSet(viewsets.ViewSet):

    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        JSONParser,
    ]

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(
            **kwargs
        )

        self.service = DocumentService()

    def create(
        self,
        request,
    ):
        serializer = DocumentUploadSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        document = self.service.upload_document(
            uploaded_file=serializer.validated_data[
                "file"
            ],
            owner=request.user,
        )

        return Response(
            DocumentSerializer(
                document
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(
        self,
        request,
        pk=None,
    ):
        try:
            document = self.service.get_document(
                pk
            )

        except Exception:
            return Response(
                {
                    "detail": "Document not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if document.owner_id != request.user.id:
            return Response(
                {
                    "detail": "Document not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DocumentSerializer(
            document
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def list(
        self,
        request,
    ):
        min_confidence = request.query_params.get(
            "min_confidence"
        )

        if min_confidence is not None:
            try:
                min_confidence = float(
                    min_confidence
                )

            except ValueError:
                return Response(
                    {
                        "detail": (
                            "min_confidence must be "
                            "a valid number."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        documents = self.service.list_documents(
            owner=request.user,
            status=request.query_params.get(
                "status"
            ),
            document_type=request.query_params.get(
                "document_type"
            ),
            search=request.query_params.get(
                "search"
            ),
            min_confidence=min_confidence,
        )

        paginator = PageNumberPagination()

        page = paginator.paginate_queryset(
            documents,
            request,
            view=self,
        )

        serializer = DocumentSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    @action(
        detail=True,
        methods=[
            "post",
        ],
        url_path="retry",
    )
    def retry(
        self,
        request,
        pk=None,
    ):
        try:
            document = self.service.retry_document(
                document_id=pk,
                owner=request.user,
            )

        except DocumentNotFoundError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except DocumentRetryNotAllowedError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "message": (
                    "Document processing retry "
                    "has been queued."
                ),
                "document": DocumentSerializer(
                    document
                ).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )
        
    @action(
        detail=True,
        methods=[
            "get",
        ],
        url_path="history",
    )
    def history(
        self,
        request,
        pk=None,
    ):
        try:
            processing_logs = (
                self.service
                .get_processing_history(
                    document_id=pk,
                    owner=request.user,
                )
            )

        except DocumentNotFoundError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            DocumentProcessingLogSerializer(
                processing_logs,
                many=True,
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )  