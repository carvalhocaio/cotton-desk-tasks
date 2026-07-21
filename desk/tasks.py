import time
from decimal import Decimal

from django.tasks import task

from desk.domain import ParametroHVIInvalido
from desk.extracao import extrair_dados_confirmacao
from desk.models import Contrato, Fardo, IndicePreco, LaudoHVI


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
    round-trip — quem chama essa task precisa converter antes.
    """
    leitura, _criada = IndicePreco.objects.update_or_create(
        codigo=codigo,
        data_pregao=data_pregao,
        defaults={"valor": Decimal(valor)},
    )
    return f"{leitura.codigo} em {leitura.data_pregao}: R$ {leitura.valor}"


@task(queue_name="confirmacoes", priority=30)
def extrair_confirmacao(texto: str) -> str:
    """Extrai dados de um texto livre, cria o Contrato e agenda a confirmação formal.

    Se o fardo citado no texto não existir na base, a task falha com
    `Fardo.DoesNotExist` — um LLM pode alucinar ou errar o código, e isso
    deve aparecer como falha real, não ser engolido silenciosamente.
    """
    dados = extrair_dados_confirmacao(texto)
    fardo = Fardo.objects.get(codigo=dados.fardo_codigo)
    contrato = Contrato.objects.create(
        fardo=fardo,
        comprador=dados.comprador,
        preco_por_kg=Decimal(dados.preco_por_kg),
    )
    confirmar_contrato.enqueue(contrato.id)
    return f"Contrato {contrato.id} criado: fardo {fardo.codigo}, comprador {contrato.comprador}"

@task(queue_name="demo", priority=0)
def tarefa_de_demonstracao() -> str:
    """Task artificialmente lenta, só para o painel exibir o estado 'executando'.

    O `sleep` aqui é intencional e honesto: simular latência É a função desta
    task. Ela não tem papel no negócio — existe apenas para tornar visível no
    dashboard a transição READY → RUNNING → SUCCESSFUL, que nas tasks reais
    (rápidas) acontece rápido demais para o olho acompanhar.
    """
    time.sleep(4)
    return "demonstração concluída após 4s de execução simulada"