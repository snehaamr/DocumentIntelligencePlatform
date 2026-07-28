from django.urls import path

from .views import (
    DocumentUploadView,
    ProcessDocumentView,
)


urlpatterns = [

    path(
        "upload/",
        DocumentUploadView.as_view(),
        name="upload-document"
    ),


    path(
        "<uuid:document_id>/process/",
        ProcessDocumentView.as_view(),
        name="process-document"
    ),

]