import csv
import io
from functools import partial

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.tasks import TaskResultStatus, default_task_backend
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django_tasks_db.models import DBTaskResult

from desk.models import Contrato, Fardo, LaudoHVI
from desk.tasks import confirmar_contrato
from desk.tasks import resumir_laudo as tarefa_resumir_laudo


@csrf_exempt
@require_POST
def resumir_laudo(request, laudo_id):
    """Enfileira o resumo de um laudo HVI e devolve o id da task."""
    resultado = tarefa_resumir_laudo.enqueue(laudo_id)
    return JsonResponse({"task_id": str(resultado.id)}, status=202)


@require_GET
def status_da_task(request, task_id):
    """Consulta o status de uma task já enfileirada."""
    resultado = default_task_backend.get_result(task_id)
    resultado.refresh()

    if resultado.status == TaskResultStatus.SUCCESSFUL:
        return JsonResponse({"status": "concluida", "resultado": resultado.return_value})

    if resultado.status == TaskResultStatus.FAILED:
        erro = resultado.errors[0].exception_class_path
        return JsonResponse({"status": "falhou", "erro": erro}, status=422)

    return JsonResponse({"status": "pendente"})


@csrf_exempt
@require_POST
def checkout(request):
    """Fecha um contrato e agenda a confirmação para depois do commit."""
    fardo = Fardo.objects.get(pk=request.POST["fardo_id"])
    with transaction.atomic():
        contrato = Contrato.objects.create(
            fardo=fardo,
            comprador=request.POST["comprador"],
            preco_por_kg=request.POST["preco_por_kg"],
        )
        transaction.on_commit(partial(confirmar_contrato.enqueue, contrato.id))
    return JsonResponse({"contrato_id": contrato.id}, status=201)


@csrf_exempt
@require_POST
def upload_lote_laudos(request):
    """Recebe um CSV de laudos HVI, persiste cada linha e enfileira o resumo.

    Atalho de demonstração: usa `get_or_create` por código de fardo para que
    o mesmo CSV possa ser reenviado em testes manuais sem estourar por
    unicidade — não é a regra real de deduplicação de fardo.
    """
    arquivo = request.FILES["arquivo"]
    texto = io.TextIOWrapper(arquivo.file, encoding="utf-8")
    leitor = csv.DictReader(texto)

    task_ids = []
    criados = 0
    for linha in leitor:
        fardo, _fardo_criado = Fardo.objects.get_or_create(
            codigo=linha["codigo"],
            defaults={
                "safra": linha["safra"],
                "produtor": linha["produtor"],
                "peso_kg": linha["peso_kg"],
                "data_classificacao": linha["data_classificacao"],
            },
        )
        laudo = LaudoHVI.objects.create(
            fardo=fardo,
            micronaire=linha["micronaire"],
            comprimento=linha["comprimento"],
            resistencia=linha["resistencia"],
            uniformidade=linha["uniformidade"],
        )
        resultado = tarefa_resumir_laudo.enqueue(laudo.id)
        task_ids.append(str(resultado.id))
        criados += 1

    return JsonResponse({"criados": criados, "task_ids": task_ids}, status=202)


@require_GET
def tasks_json(request):
    """Lista as tasks mais recentes por fila, para o dashboard consumir via polling."""
    tasks = DBTaskResult.objects.order_by("-enqueued_at")[:50]
    dados = [
        {
            "id": str(t.id),
            "fila": t.queue_name,
            "tarefa": t.task_path.rsplit(".", 1)[-1],
            "status": t.status,
            "enfileirada_em": t.enqueued_at.isoformat() if t.enqueued_at else None,
            "iniciada_em": t.started_at.isoformat() if t.started_at else None,
            "finalizada_em": t.finished_at.isoformat() if t.finished_at else None,
        }
        for t in tasks
    ]
    return JsonResponse({"tasks": dados})


def dashboard(request):
    """Renderiza o painel visual das filas — apresentação pura, sem lógica de negócio."""
    return render(request, "desk/dashboard.html")
