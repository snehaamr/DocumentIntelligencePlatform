from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = (
        "original_filename",
        "document_type",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "document_type",
    )

    search_fields = (
        "original_filename",
        "document_type",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )