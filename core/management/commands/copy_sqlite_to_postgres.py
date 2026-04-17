from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, CommandError, call_command
from django.core.management.color import no_style
from django.db import connections, transaction

from core.models import AffiliateClick, Calculation, Lead


class Command(BaseCommand):
    help = "Copy data from the legacy SQLite database into PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default="sqlite",
            help="Source database alias. Defaults to the legacy SQLite alias.",
        )
        parser.add_argument(
            "--target",
            default="default",
            help="Target database alias. Defaults to the primary PostgreSQL database.",
        )
        parser.add_argument(
            "--flush-target",
            action="store_true",
            help="Delete existing target data before copying.",
        )

    def handle(self, *args, **options):
        source_alias = options["source"]
        target_alias = options["target"]
        flush_target = options["flush_target"]

        if source_alias not in connections:
            raise CommandError(
                f"Source database alias '{source_alias}' is not configured."
            )
        if target_alias not in connections:
            raise CommandError(
                f"Target database alias '{target_alias}' is not configured."
            )

        source_connection = connections[source_alias]
        if source_connection.vendor != "sqlite":
            raise CommandError(
                f"Source database '{source_alias}' must point to the legacy SQLite database."
            )

        User = get_user_model()
        models_to_copy = [
            User,
            User.groups.through,
            User.user_permissions.through,
            Calculation,
            AffiliateClick,
            Lead,
        ]

        call_command("migrate", database=target_alias, interactive=False, verbosity=0)

        with transaction.atomic(using=target_alias):
            if flush_target:
                for model in reversed(models_to_copy):
                    model.objects.using(target_alias).all().delete()

            self._raise_if_target_has_data(models_to_copy, target_alias, flush_target)

            for model in models_to_copy:
                self._copy_model(model, source_alias, target_alias)

            self._reset_sequences(models_to_copy, target_alias)

        self.stdout.write(self.style.SUCCESS("SQLite data copied to PostgreSQL."))

    def _raise_if_target_has_data(self, models_to_copy, target_alias, flush_target):
        if flush_target:
            return

        existing_models = [
            model._meta.label
            for model in models_to_copy
            if model.objects.using(target_alias).exists()
        ]
        if existing_models:
            raise CommandError(
                "Target database already has data for: "
                + ", ".join(existing_models)
                + ". Re-run with --flush-target to replace the target contents."
            )

    def _copy_model(self, model, source_alias, target_alias):
        field_names = [field.attname for field in model._meta.concrete_fields]
        rows = []

        for source_object in (
            model.objects.using(source_alias).all().iterator(chunk_size=1000)
        ):
            row_data = {
                field_name: getattr(source_object, field_name)
                for field_name in field_names
            }
            rows.append(model(**row_data))

        if rows:
            model.objects.using(target_alias).bulk_create(rows, batch_size=1000)

    def _reset_sequences(self, models_to_copy, target_alias):
        connection = connections[target_alias]
        sequence_sql = connection.ops.sequence_reset_sql(no_style(), models_to_copy)
        if sequence_sql:
            with connection.cursor() as cursor:
                for statement in sequence_sql:
                    cursor.execute(statement)
