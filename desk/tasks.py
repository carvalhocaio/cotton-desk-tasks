from decimal import Decimal

from django.tasks import task

from desk.domain import ParametroHVIInvalido
from desk.models import Contrato, IndicePreco, LaudoHVI


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


@task(queue_name="confirmacoes", priority=50)
def confirmar_contrato(contrato_id: int) -> str:
    """Gera a confirmação textual de um contrato recém-fechado."""
    contrato = Contrato.objects.select_related("fardo").get(pk=contrato_id)
    return (
        f"Contrato do fardo {contrato.fardo.codigo} confirmado com "
        f"{contrato.comprador} a R$ {contrato.preco_por_kg}/kg"
    )


@task(queue_name="precos", priority=0)
def registrar_leitura_indice(codigo: str, valor: str, data_pregao: str) -> str:
    """Persiste uma leitura de índice de preço.

    `valor` chega como string, não Decimal: argumentos de task passam por
    serialização JSON no `.enqueue()`, e Decimal não sobrevive a esse
    round-trip; quem chama essa task precisa converter antes.
    """
    leitura, _criada = IndicePreco.objects.update_or_create(
        codigo=codigo,
        data_pregao=data_pregao,
        defaults={"valor": Decimal(valor)},
    )

    return f"{leitura.codigo} em {leitura.data_pregao}: R$ {leitura.valor}"
