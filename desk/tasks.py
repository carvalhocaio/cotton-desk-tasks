from django.tasks import task

from desk.models import LaudoHVI


@task
def resumir_laudo(laudo_id: int) -> str:
    """Resume um laudo HVI a partir dos parâmetros de domínio validados."""
    laudo = LaudoHVI.objects.get(pk=laudo_id)
    parametros = laudo.to_dominio()
    return (
        f"Fardo {laudo.fardo.codigo}: micronaire {parametros.micronaire}, "
        f'comprimento {parametros.comprimento}", '
        f"resistência {parametros.resistencia} gf/tex, "
        f"uniformidade {parametros.uniformidade}%"
    )
