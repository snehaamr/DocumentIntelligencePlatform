from pathlib import Path
import mimetypes

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from apps.documents.models import Document
from apps.documents.tasks import process_document_task


User = get_user_model()


class Command(BaseCommand):

    help = (
        "Import existing files from media/documents, "
        "assign them to a user, and queue them for processing."
    )

    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "--username",
            type=str,
            required=True,
            help=(
                "Username of the user who will own "
                "the imported documents."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):

        username = options["username"]

        try:
            owner = User.objects.get(
                username=username
            )
        except User.DoesNotExist as exc:
            raise CommandError(
                f'User "{username}" does not exist.'
            ) from exc

        documents_directory = (
            Path(settings.MEDIA_ROOT)
            / "documents"
        )

        if not documents_directory.exists():
            raise CommandError(
                f"Directory does not exist: "
                f"{documents_directory}"
            )

        if not documents_directory.is_dir():
            raise CommandError(
                f"Path is not a directory: "
                f"{documents_directory}"
            )

        imported = 0
        queued = 0
        skipped = 0

        for file_path in sorted(
            documents_directory.iterdir()
        ):

            if not file_path.is_file():
                continue

            relative_path = (
                f"documents/{file_path.name}"
            )

            existing_document = (
                Document.objects.filter(
                    owner=owner,
                    uploaded_file=relative_path,
                ).first()
            )

            if existing_document:

                skipped += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping existing document: "
                        f"{file_path.name}"
                    )
                )

                continue

            mime_type, _ = (
                mimetypes.guess_type(
                    file_path.name
                )
            )

            document = Document.objects.create(
                owner=owner,
                original_filename=file_path.name,
                uploaded_file=relative_path,
                mime_type=(
                    mime_type
                    or "application/octet-stream"
                ),
                file_size=file_path.stat().st_size,
                status="UPLOADED",
            )

            imported += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Imported document "
                    f"{document.id}: "
                    f"{file_path.name}"
                )
            )

            process_document_task.delay(
                str(document.id)
            )

            queued += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Queued document "
                    f"{document.id} for processing"
                )
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"Owner: {owner.username}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported: {imported}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Queued: {queued}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Skipped: {skipped}"
            )
        )