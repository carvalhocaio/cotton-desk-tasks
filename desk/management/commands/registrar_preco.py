from django.core.management.base import BaseCommand

from desk.tasks import registrar_leitura_indice


class Command(BaseCommand):
    help = "Enfileira o registro de uma leitura de índice de preço (ex.: para rodar via cron)."

    def add_arguments(self, parser):
        parser.add_argument("codigo", type=str, help="Código do índice, ex.: ICE-CT2")
        parser.add_argument("valor", type=str, help="Valor da leitura, ex.: 82.35")
        parser.add_argument("data_pregao", type=str, help="Data do pregão, formato YYYY-MM-DD")

    def handle(self, *args, **options):
        resultado = registrar_leitura_indice.enqueue(
            options["codigo"], options["valor"], options["data_pregao"]
        )
        self.stdout.write(
            self.style.SUCCESS(f"Enfileirado: task_id={resultado.id}")
        )
