from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = (
        "filename",
        "status",
        "document_type",
        "created_at",
    )

    search_fields = (
        "filename",
        "document_type",
    )

    list_filter = (
        "status",
        "document_type",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )