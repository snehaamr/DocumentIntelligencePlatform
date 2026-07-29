from django.contrib.auth import get_user_model
from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from apps.documents.models import Document
from services.tasks import process_document_task


User = get_user_model()


class Command(BaseCommand):

    help = (
        "Queue existing uploaded documents "
        "for background processing."
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
                "Queue documents belonging "
                "to this username."
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

        documents = Document.objects.filter(
            owner=owner,
            status="UPLOADED",
        ).order_by(
            "created_at"
        )

        document_count = documents.count()

        if document_count == 0:
            self.stdout.write(
                self.style.WARNING(
                    "No UPLOADED documents found."
                )
            )
            return

        queued = 0

        for document in documents:

            process_document_task.delay(
                str(document.id)
            )

            queued += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Queued document "
                    f"{document.id}: "
                    f"{document.original_filename}"
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
                f"Queued: {queued}"
            )
        )