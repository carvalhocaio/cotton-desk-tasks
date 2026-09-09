from django.core.management.base import BaseCommand

from desk.tasks import record_index_reading


class Command(BaseCommand):
    help = "Enqueues the recording of a price index reading (e.g. to run via cron)."

    def add_arguments(self, parser):
        parser.add_argument("code", type=str, help="Index code, e.g. ICE-CT2")
        parser.add_argument("value", type=str, help="Reading value, e.g. 82.35")
        parser.add_argument(
            "trading_date", type=str, help="Trading date, YYYY-MM-DD format"
        )

    def handle(self, *args, **options):
        result = record_index_reading.enqueue(
            options["code"], options["value"], options["trading_date"]
        )
        self.stdout.write(self.style.SUCCESS(f"Enqueued: task_id={result.id}"))
