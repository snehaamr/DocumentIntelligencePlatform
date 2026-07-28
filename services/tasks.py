from celery import shared_task

from services.document_service import DocumentService


@shared_task
def process_document_task(document_id):

    service = DocumentService()

    document = service.process_document(
        document_id
    )

    return {
        "document_id": str(document.id),
        "status": document.status
    }