from django.tasks import task

from desk.domain import ParametroHVIInvalido
from desk.models import LaudoHVI


@task(queue_name="laudos", priority=50)
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


@task(queue_name="relatorios", priority=-10)
def gerar_relatorio_safra(safra: str) -> str:
    """Consolida quantos laudos de uma safra são comercialmente válidos."""
    laudos = LaudoHVI.objects.filter(fardo__safra=safra)
    total = laudos.count()
    validos = 0
    invalidos = 0
    for laudo in laudos:
        try:
            laudo.to_dominio()
            validos += 1
        except ParametroHVIInvalido:
            invalidos += 1
    return f"Safra {safra}: {total} laudos, {validos} válido(s), {invalidos} inválido(s)"
